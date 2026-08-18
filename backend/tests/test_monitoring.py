from datetime import UTC, datetime

import httpx
from test_devices import DEVICE

from app.models import Device, DeviceKind
from app.prometheus import PrometheusClient, prometheus_client
from app.schemas import DeviceMetric, MonitoringSummary


def fake_summary(devices):
    return MonitoringSummary(
        available=True,
        checked_at=datetime.now(UTC),
        total_devices=len(devices),
        online_devices=len(devices),
        offline_devices=0,
        unknown_devices=0,
        firing_alerts=0,
        devices=[
            DeviceMetric(
                device_id=device.id,
                status="online",
                cpu_percent=42.5,
                memory_percent=61.0,
                disk_percent=35.0,
            )
            for device in devices
        ],
    )


def test_summary_combines_inventory_and_monitoring(admin_client, monkeypatch):
    created = admin_client.post("/api/v1/devices", json=DEVICE)
    assert created.status_code == 201
    monkeypatch.setattr(prometheus_client, "summary", fake_summary)

    response = admin_client.get("/api/v1/monitoring/summary")

    assert response.status_code == 200
    assert response.json()["online_devices"] == 1
    assert response.json()["devices"][0]["cpu_percent"] == 42.5


def test_csv_report_contains_status_and_utf8_bom(admin_client, monkeypatch):
    assert admin_client.post("/api/v1/devices", json=DEVICE).status_code == 201
    monkeypatch.setattr(prometheus_client, "summary", fake_summary)

    response = admin_client.get("/api/v1/reports/status.csv")

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert response.content.startswith(b"\xef\xbb\xbf")
    assert "Server Aplikasi" in response.content.decode("utf-8-sig")


def test_prometheus_summary_maps_machine_metrics(monkeypatch):
    client = PrometheusClient("http://prometheus.test")
    device = Device(
        id=7,
        name="Server Uji",
        kind=DeviceKind.LINUX_SERVER.value,
        address="10.0.0.7",
        prometheus_job="node",
        prometheus_target="10.0.0.7:9100",
    )

    def query(expression):
        value = "1"
        if "cpu_seconds" in expression:
            value = "42.4"
        elif "MemAvailable" in expression:
            value = "61.2"
        elif "filesystem" in expression:
            return [
                {"metric": {"instance": device.prometheus_target}, "value": [0, "35"]},
                {"metric": {"instance": device.prometheus_target}, "value": [0, "77"]},
            ]
        elif "boot_time" in expression:
            value = "86400"
        elif "receive" in expression:
            value = "1024"
        elif "transmit" in expression:
            value = "512"
        elif expression == "probe_success":
            return []
        return [{"metric": {"instance": device.prometheus_target}, "value": [0, value]}]

    monkeypatch.setattr(client, "query", query)
    monkeypatch.setattr(client, "alerts", lambda: [])

    summary = client.summary([device])

    assert summary.available is True
    assert summary.online_devices == 1
    assert summary.devices[0].cpu_percent == 42.4
    assert summary.devices[0].disk_percent == 77.0


def test_prometheus_summary_degrades_when_server_is_unavailable(monkeypatch):
    client = PrometheusClient("http://prometheus.test")
    device = Device(
        id=8,
        name="Server Uji",
        kind=DeviceKind.LINUX_SERVER.value,
        address="10.0.0.8",
        prometheus_job="node",
        prometheus_target="10.0.0.8:9100",
    )

    def unavailable(_expression):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(client, "query", unavailable)
    summary = client.summary([device])

    assert summary.available is False
    assert summary.unknown_devices == 1
    assert summary.devices[0].status == "unknown"


def test_alert_parser_uses_human_readable_name(monkeypatch):
    client = PrometheusClient("http://prometheus.test")
    monkeypatch.setattr(
        client,
        "_get",
        lambda _path: {
            "alerts": [
                {
                    "labels": {
                        "alertname": "RuangDiskMenipis",
                        "severity": "critical",
                        "instance": "server:9100",
                    },
                    "annotations": {"summary": "Sisa disk kurang dari 10%"},
                    "state": "firing",
                    "activeAt": "2026-08-09T00:00:00Z",
                }
            ]
        },
    )

    alerts = client.alerts()

    assert alerts[0].name == "Ruang disk menipis"
    assert alerts[0].active_since is not None
