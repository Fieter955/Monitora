import pytest

from bootstrap import bootstrap
from core.config import settings
from db.session import SessionLocal
from models.device import Device, DeviceKind
from services.auth import reset_login_limits
from services.network import get_internal_metrics
from services.probes import rtsp_probe


def test_login_rate_limiting(client):
    reset_login_limits()
    # 5 failed attempts yield 401 Unauthorized
    for _ in range(5):
        res = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrong-password"},
        )
        assert res.status_code == 401

    # 6th attempt is rate-limited: triggers 429 Too Many Requests
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )
    assert res.status_code == 429
    assert "Terlalu banyak percobaan masuk yang gagal" in res.json()["detail"]

    # Reset allows login again
    reset_login_limits()
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin-password"},
    )
    assert res.status_code == 200


def test_rtsp_stream_url_crlf_and_scheme_rejection(admin_client):
    cctv_payload = {
        "name": "Kamera Gerbang",
        "kind": "cctv",
        "address": "10.10.0.99",
        "location": "Pintu Gerbang",
        "prometheus_job": "cctv",
        "prometheus_target": "10.10.0.99:554",
        "stream_url": "rtsp://10.10.0.99:554/stream\r\nSET malicious_key evil",
    }
    # Reject CRLF in stream_url
    res = admin_client.post("/api/v1/devices", json=cctv_payload)
    assert res.status_code == 422

    # Reject non-rtsp scheme
    cctv_payload["stream_url"] = "http://10.10.0.99/live"
    res = admin_client.post("/api/v1/devices", json=cctv_payload)
    assert res.status_code == 422

    # Reject credentials in URL
    cctv_payload["stream_url"] = "rtsp://admin:pass@10.10.0.99:554/live"
    res = admin_client.post("/api/v1/devices", json=cctv_payload)
    assert res.status_code == 422

    # Direct probe also rejects CRLF
    result = rtsp_probe("rtsp://10.10.0.99:554/stream\r\nSPLIT")
    assert result.reachable is False
    assert result.status == "invalid"


def test_device_name_newline_rejection(admin_client):
    payload = {
        "name": "Server\nInjeksi",
        "kind": "linux_server",
        "address": "10.10.0.50",
        "location": "Ruang Server",
        "prometheus_job": "node",
        "prometheus_target": "10.10.0.50:9100",
    }
    res = admin_client.post("/api/v1/devices", json=payload)
    assert res.status_code == 422

    # Test update rejection as well
    valid_payload = {**payload, "name": "Server Valid"}
    created = admin_client.post("/api/v1/devices", json=valid_payload)
    assert created.status_code == 201
    device_id = created.json()["id"]

    res_patch = admin_client.patch(
        f"/api/v1/devices/{device_id}",
        json={"name": "Server\r\nUpdateInjeksi"},
    )
    assert res_patch.status_code == 422


def test_csv_report_formula_injection_sanitization(admin_client):
    formula_device = {
        "name": "=cmd|'/C calc'!A0",
        "kind": "linux_server",
        "address": "10.10.0.60",
        "location": "@HarmfulLocation",
        "prometheus_job": "node",
        "prometheus_target": "10.10.0.60:9100",
    }
    created = admin_client.post("/api/v1/devices", json=formula_device)
    assert created.status_code == 201

    csv_res = admin_client.get("/api/v1/reports/status.csv")
    assert csv_res.status_code == 200
    csv_text = csv_res.text
    # Cell starting with '=' must be sanitized to "'=cmd|'/C calc'!A0"
    assert "'=cmd|'/C calc'!A0" in csv_text
    # Cell starting with '@' must be sanitized to "'@HarmfulLocation"
    assert "'@HarmfulLocation" in csv_text


def test_prometheus_metrics_exposition_sanitizes_newlines():
    with SessionLocal() as db:
        evil_device = Device(
            name="Router\nEvilInjectedLabel",
            kind=DeviceKind.ROUTER.value,
            address="10.10.0.70",
            prometheus_job="icmp",
            prometheus_target="10.10.0.70",
            is_active=True,
        )
        db.add(evil_device)
        db.commit()

        metrics = get_internal_metrics(db)
        # The newline in name should have been replaced with a space
        assert "Router EvilInjectedLabel" in metrics
        assert "Router\nEvilInjectedLabel" not in metrics


def test_bootstrap_production_enforces_grafana_password(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "app_secret_key", "a-very-long-production-secret-key-1234567890")
    monkeypatch.setattr(settings, "admin_password", "strong-production-admin-pass-123")
    monkeypatch.setattr(
        settings, "credential_encryption_key", "different-32-character-encryption-key-ok"
    )
    monkeypatch.setattr(settings, "grafana_admin_password", "admin")

    with pytest.raises(
        RuntimeError, match="GRAFANA_ADMIN_PASSWORD wajib diisi dan diganti untuk production"
    ):
        bootstrap()
