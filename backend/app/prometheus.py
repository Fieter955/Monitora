from datetime import UTC, datetime
from typing import Any

import httpx

from app.config import settings
from app.models import Device
from app.schemas import AlertRead, DeviceMetric, MonitoringSummary

ALERT_DISPLAY_NAMES = {
    "TargetTidakTerjangkau": "Target tidak terjangkau",
    "PenggunaanCPUtinggi": "Penggunaan CPU tinggi",
    "PenggunaanMemoriTinggi": "Penggunaan memori tinggi",
    "RuangDiskMenipis": "Ruang disk menipis",
    "WebsiteTidakTersedia": "Website tidak tersedia",
    "SertifikatSegeraBerakhir": "Sertifikat segera berakhir",
    "PortWajibTerputus": "Port wajib terputus",
    "PerangkatAsingTerdeteksi": "Perangkat asing terdeteksi",
    "StreamCCTVTerputus": "Stream CCTV terputus",
    "DataJaringanTerlambat": "Data jaringan terlambat",
    "PerangkatJaringanTidakTerjangkau": "Perangkat jaringan tidak terjangkau",
    "PerangkatLANOffline": "Perangkat LAN offline",
}

def _metric_map(result: list[dict[str, Any]], *, use_max: bool = False) -> dict[str, float]:
    values: dict[str, float] = {}
    for item in result:
        instance = item.get("metric", {}).get("instance")
        raw_value = item.get("value", [None, None])[1]
        if instance and raw_value is not None:
            try:
                value = float(raw_value)
                values[instance] = max(values.get(instance, value), value) if use_max else value
            except (TypeError, ValueError):
                continue
    return values


class PrometheusClient:
    def __init__(self, base_url: str = settings.prometheus_url) -> None:
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        with httpx.Client(timeout=4.0) as client:
            response = client.get(f"{self.base_url}{path}", params=params)
            response.raise_for_status()
            payload = response.json()
        if payload.get("status") != "success":
            raise RuntimeError(payload.get("error", "Respons Prometheus tidak valid"))
        return payload.get("data")

    def query(self, expression: str) -> list[dict[str, Any]]:
        data = self._get("/api/v1/query", {"query": expression})
        return data.get("result", []) if isinstance(data, dict) else []

    def summary(self, devices: list[Device]) -> MonitoringSummary:
        checked_at = datetime.now(UTC)
        if not devices:
            return MonitoringSummary(
                available=True,
                checked_at=checked_at,
                total_devices=0,
                online_devices=0,
                offline_devices=0,
                unknown_devices=0,
                firing_alerts=0,
                devices=[],
            )

        try:
            up = _metric_map(self.query("up"))
            probe = _metric_map(self.query("probe_success"))
            cpu = _metric_map(
                self.query(
                    '100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
                )
            )
            memory = _metric_map(
                self.query(
                    "100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))"
                )
            )
            disk = _metric_map(
                self.query(
                    '100 * (1 - (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} '
                    '/ node_filesystem_size_bytes{fstype!~"tmpfs|overlay"}))'
                ),
                use_max=True,
            )
            uptime = _metric_map(self.query("time() - node_boot_time_seconds"))
            receive = _metric_map(
                self.query(
                    "sum by(instance) (rate(node_network_receive_bytes_total"
                    '{device!~"lo|veth.*"}[5m])) or '
                    "sum by(instance) (rate(ifHCInOctets[5m]))"
                )
            )
            transmit = _metric_map(
                self.query(
                    "sum by(instance) (rate(node_network_transmit_bytes_total"
                    '{device!~"lo|veth.*"}[5m])) or '
                    "sum by(instance) (rate(ifHCOutOctets[5m]))"
                )
            )
            alerts = self.alerts()
        except (httpx.HTTPError, RuntimeError, ValueError) as exc:
            return MonitoringSummary(
                available=False,
                checked_at=checked_at,
                total_devices=len(devices),
                online_devices=0,
                offline_devices=0,
                unknown_devices=len(devices),
                firing_alerts=0,
                devices=[DeviceMetric(device_id=device.id, status="unknown") for device in devices],
                message=f"Prometheus belum dapat dihubungi: {exc}",
            )

        metrics: list[DeviceMetric] = []
        for device in devices:
            target = device.prometheus_target
            up_value = (
                probe.get(target)
                if device.prometheus_job in {"icmp", "blackbox"}
                else up.get(target)
            )
            status = "online" if up_value == 1 else "offline" if up_value == 0 else "unknown"
            metrics.append(
                DeviceMetric(
                    device_id=device.id,
                    status=status,
                    cpu_percent=_rounded(cpu.get(target)),
                    memory_percent=_rounded(memory.get(target)),
                    disk_percent=_max_rounded(disk, target),
                    uptime_seconds=_rounded(uptime.get(target)),
                    receive_bytes_per_second=_rounded(receive.get(target)),
                    transmit_bytes_per_second=_rounded(transmit.get(target)),
                )
            )

        return MonitoringSummary(
            available=True,
            checked_at=checked_at,
            total_devices=len(devices),
            online_devices=sum(item.status == "online" for item in metrics),
            offline_devices=sum(item.status == "offline" for item in metrics),
            unknown_devices=sum(item.status == "unknown" for item in metrics),
            firing_alerts=sum(item.state == "firing" for item in alerts),
            devices=metrics,
        )

    def alerts(self) -> list[AlertRead]:
        data = self._get("/api/v1/alerts")
        raw_alerts = data.get("alerts", []) if isinstance(data, dict) else []
        alerts: list[AlertRead] = []
        for item in raw_alerts:
            labels = item.get("labels", {})
            annotations = item.get("annotations", {})
            active_at = item.get("activeAt")
            try:
                parsed_active_at = datetime.fromisoformat(active_at.replace("Z", "+00:00"))
            except (AttributeError, ValueError):
                parsed_active_at = None
            alerts.append(
                AlertRead(
                    name=ALERT_DISPLAY_NAMES.get(
                        labels.get("alertname", ""), labels.get("alertname", "Alert tanpa nama")
                    ),
                    severity=labels.get("severity", "warning"),
                    state=item.get("state", "unknown"),
                    instance=labels.get("instance", labels.get("job", "-")),
                    summary=annotations.get("summary", annotations.get("description", "")),
                    active_since=parsed_active_at,
                    device_id=(
                        int(labels["device_id"])
                        if str(labels.get("device_id", "")).isdigit()
                        else None
                    ),
                )
            )
        return alerts


def _rounded(value: float | None) -> float | None:
    return round(value, 2) if value is not None else None


def _max_rounded(values: dict[str, float], target: str) -> float | None:
    value = values.get(target)
    return _rounded(value)


prometheus_client = PrometheusClient()
