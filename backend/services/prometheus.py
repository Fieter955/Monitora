from datetime import UTC, datetime
from typing import Any

import httpx

from core.config import settings
from models.device import Device, NetworkRole
from schemas.monitoring import (
    AlertRead,
    DeviceMetric,
    InternetHealth,
    MonitoringSummary,
    SnmpInterfaceRead,
)

ALERT_DISPLAY_NAMES = {
    "TargetTidakTerjangkau": "Target tidak terjangkau",
    "PenggunaanCPUtinggi": "Penggunaan CPU tinggi",
    "PenggunaanMemoriTinggi": "Penggunaan memori tinggi",
    "RuangDiskMenipis": "Ruang disk menipis",
    "RuangDiskKritis": "Ruang disk kritis",
    "PenggunaanCPUKritis": "Penggunaan CPU kritis",
    "PenggunaanMemoriKritis": "Penggunaan memori kritis",
    "WebsiteTidakTersedia": "Website tidak tersedia",
    "SertifikatSegeraBerakhir": "Sertifikat segera berakhir",
    "PortWajibTerputus": "Port wajib terputus",
    "PerangkatAsingTerdeteksi": "Perangkat asing terdeteksi",
    "StreamCCTVTerputus": "Stream CCTV terputus",
    "DataJaringanTerlambat": "Data jaringan terlambat",
    "PerangkatJaringanTidakTerjangkau": "Perangkat jaringan tidak terjangkau",
    "PerangkatLANOffline": "Perangkat LAN offline",
    "GangguanISP": "Gangguan ISP terindikasi",
    "LinkWANPutus": "Link WAN terputus",
    "GangguanDNS": "Layanan DNS bermasalah",
    "ServiceWindowsBerhenti": "Service Windows berhenti",
}
SUMMARY_QUERIES: dict[str, tuple[str, bool]] = {
    "up": ("up", False),
    "probe": ("probe_success", False),
    "cpu": (
        '(100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)) or '
        '(100 - (avg by(instance) (rate(windows_cpu_time_total{mode="idle"}[5m])) * 100))',
        False,
    ),
    "memory": (
        "100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) or "
        "100 * (1 - (windows_memory_available_bytes / windows_memory_physical_total_bytes)) or "
        "100 * (1 - (windows_memory_available_bytes / windows_cs_physical_memory_bytes))",
        False,
    ),
    "disk": (
        '(100 * (1 - (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} '
        '/ node_filesystem_size_bytes{fstype!~"tmpfs|overlay"}))) or '
        '(100 * (1 - (windows_logical_disk_free_bytes{volume!="_Total"} '
        '/ windows_logical_disk_size_bytes{volume!="_Total"})))',
        True,
    ),
    "uptime": (
        "(time() - node_boot_time_seconds) or "
        "(time() - windows_system_boot_time_timestamp) or (time() - windows_system_system_up_time)",
        False,
    ),
    "receive": (
        'sum by(instance) (rate(node_network_receive_bytes_total{device!~"lo|veth.*"}[5m])) or '
        "sum by(instance) (rate(windows_net_bytes_received_total[5m])) or "
        "sum by(instance) (rate(ifHCInOctets[5m]))",
        False,
    ),
    "transmit": (
        'sum by(instance) (rate(node_network_transmit_bytes_total{device!~"lo|veth.*"}[5m])) or '
        "sum by(instance) (rate(windows_net_bytes_sent_total[5m])) or "
        "sum by(instance) (rate(ifHCOutOctets[5m]))",
        False,
    ),
}


def _promql_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


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


def _diagnose_internet_state(
    gateway_up: bool | None,
    wan_up: bool | None,
    internet_ip: bool | None,
    dns: bool | None,
    https: bool | None,
) -> tuple[str, str, str]:
    if gateway_up is False:
        msg = "Gateway MikroTik tidak terjangkau dari server monitoring."
        return ("critical", "lan_or_router", msg)
    if wan_up is False:
        return ("critical", "wan_link", "Interface WAN MikroTik dalam kondisi down.")
    if internet_ip is False:
        msg = "Gateway aktif, tetapi target internet independen tidak dapat dijangkau."
        return ("critical", "isp_upstream", msg)
    if dns is False:
        return ("warning", "dns", "Akses IP internet berhasil, tetapi pemeriksaan DNS gagal.")
    if https is False:
        return ("warning", "https", "Internet dan DNS aktif, tetapi pemeriksaan HTTPS gagal.")
    if all(value is True for value in (gateway_up, internet_ip, dns, https)):
        return ("healthy", "none", "Jalur internet dan layanan dasar berjalan normal.")
    return ("unknown", "unknown", "Data diagnosis internet belum lengkap.")


def _build_device_metric(device: Device, maps: dict[str, dict[str, float]]) -> DeviceMetric:
    target = device.prometheus_target
    up_map = maps["probe"] if device.prometheus_job in {"icmp", "blackbox"} else maps["up"]
    up_value = up_map.get(target)
    status = "online" if up_value == 1 else "offline" if up_value == 0 else "unknown"
    return DeviceMetric(
        device_id=device.id, status=status,
        cpu_percent=_rounded(maps["cpu"].get(target)),
        memory_percent=_rounded(maps["memory"].get(target)),
        disk_percent=_max_rounded(maps["disk"], target),
        uptime_seconds=_rounded(maps["uptime"].get(target)),
        receive_bytes_per_second=_rounded(maps["receive"].get(target)),
        transmit_bytes_per_second=_rounded(maps["transmit"].get(target)),
    )


class PrometheusClient:
    def __init__(self, base_url: str = settings.prometheus_url) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=4.0)

    def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        response = self._client.get(f"{self.base_url}{path}", params=params)
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "success":
            raise RuntimeError(payload.get("error", "Respons Prometheus tidak valid"))
        return payload.get("data")

    def query(self, expression: str) -> list[dict[str, Any]]:
        data = self._get("/api/v1/query", {"query": expression})
        return data.get("result", []) if isinstance(data, dict) else []

    def snmp_interfaces(self, target: str) -> list[SnmpInterfaceRead]:
        escaped = _promql_string(target)
        series = self._get("/api/v1/series", {"match[]": f'ifOperStatus{{instance="{escaped}"}}'})
        results: dict[int, SnmpInterfaceRead] = {}
        for labels in series if isinstance(series, list) else []:
            try:
                if_index = int(labels.get("ifIndex", ""))
            except (TypeError, ValueError):
                continue
            if_name = labels.get("ifName") or labels.get("ifDescr") or str(if_index)
            results[if_index] = SnmpInterfaceRead(
                if_index=if_index,
                if_name=if_name,
                if_description=labels.get("ifDescr", ""),
                if_alias=labels.get("ifAlias", ""),
            )
        if results:
            for item in self.query(f'ifOperStatus{{instance="{escaped}"}}'):
                labels = item.get("metric", {})
                try:
                    interface = results.get(int(labels.get("ifIndex", "")))
                    value = float(item.get("value", [None, None])[1])
                except (TypeError, ValueError, IndexError):
                    continue
                if interface is not None:
                    interface.oper_up = value == 1
        return sorted(results.values(), key=lambda item: (item.if_index, item.if_name.casefold()))

    def internet_health(self, devices: list[Device], checked_at: datetime) -> InternetHealth | None:
        gateway = next(
            (d for d in devices if d.network_role == NetworkRole.GATEWAY.value and d.is_active),
            None,
        )
        if gateway is None:
            return None
        gateway_up = _single_bool(
            self.query(f'probe_success{{job="gateway",device_id="{gateway.id}"}}')
        )
        wan_up: bool | None = None
        if gateway.wan_if_name:
            target = _promql_string(gateway.prometheus_target)
            if_name = _promql_string(gateway.wan_if_name)
            wan_up = _single_bool(
                self.query(f'ifOperStatus{{instance="{target}",ifName="{if_name}"}} == 1')
            )
        internet_ip = _any_bool(self.query('probe_success{job="internet-ip"}'))
        dns = _single_bool(self.query('probe_success{job="internet-dns"}'))
        https = _single_bool(self.query('probe_success{job="internet-https"}'))
        status, cause, summary = _diagnose_internet_state(
            gateway_up, wan_up, internet_ip, dns, https
        )
        return InternetHealth(
            status=status, cause=cause, summary=summary, gateway_device_id=gateway.id,
            gateway_reachable=gateway_up, wan_oper_up=wan_up, internet_ip_reachable=internet_ip,
            dns_reachable=dns, https_reachable=https, checked_at=checked_at,
        )

    def summary(self, devices: list[Device]) -> MonitoringSummary:
        checked_at = datetime.now(UTC)
        if not devices:
            return MonitoringSummary(
                available=True, checked_at=checked_at, total_devices=0, online_devices=0,
                offline_devices=0, unknown_devices=0, firing_alerts=0, devices=[],
            )
        try:
            maps = {
                key: _metric_map(self.query(expr), use_max=use_max)
                for key, (expr, use_max) in SUMMARY_QUERIES.items()
            }
            alerts = self.alerts()
            internet_health = self.internet_health(devices, checked_at)
        except (httpx.HTTPError, RuntimeError, ValueError) as exc:
            return MonitoringSummary(
                available=False, checked_at=checked_at, total_devices=len(devices),
                online_devices=0, offline_devices=0, unknown_devices=len(devices), firing_alerts=0,
                devices=[DeviceMetric(device_id=d.id, status="unknown") for d in devices],
                message=f"Prometheus belum dapat dihubungi: {exc}",
            )
        metrics = [_build_device_metric(device, maps) for device in devices]
        return MonitoringSummary(
            available=True, checked_at=checked_at, total_devices=len(devices),
            online_devices=sum(item.status == "online" for item in metrics),
            offline_devices=sum(item.status == "offline" for item in metrics),
            unknown_devices=sum(item.status == "unknown" for item in metrics),
            firing_alerts=sum(item.state == "firing" for item in alerts),
            devices=metrics, internet_health=internet_health,
        )

    def alerts(self) -> list[AlertRead]:
        try:
            data = self._get("/api/v1/alerts")
        except (httpx.HTTPError, RuntimeError):
            return []
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
            raw_id = str(labels.get("device_id", ""))
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
                    device_id=int(labels["device_id"]) if raw_id.isdigit() else None,
                )
            )
        return alerts


def _rounded(value: float | None) -> float | None:
    return round(value, 2) if value is not None else None


def _max_rounded(values: dict[str, float], target: str) -> float | None:
    return _rounded(values.get(target))


def _single_bool(result: list[dict[str, Any]]) -> bool | None:
    if not result:
        return None
    try:
        return float(result[0].get("value", [None, None])[1]) == 1
    except (TypeError, ValueError, IndexError):
        return None


def _any_bool(result: list[dict[str, Any]]) -> bool | None:
    if not result:
        return None
    known = [v for v in (_single_bool([item]) for item in result) if v is not None]
    return any(known) if known else None


prometheus_client = PrometheusClient()
