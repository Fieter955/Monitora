DEVICE = {
    "name": "Server Aplikasi",
    "kind": "linux_server",
    "address": "10.10.0.12",
    "location": "Ruang Server",
    "prometheus_job": "node",
    "prometheus_target": "10.10.0.12:9100",
    "notes": "Server layanan internal",
    "is_active": True,
}


def test_admin_can_create_update_and_delete_device(admin_client):
    created = admin_client.post("/api/v1/devices", json=DEVICE)
    assert created.status_code == 201
    device_id = created.json()["id"]

    updated = admin_client.patch(
        f"/api/v1/devices/{device_id}",
        json={"location": "Ruang Server Utama"},
    )
    assert updated.status_code == 200
    assert updated.json()["location"] == "Ruang Server Utama"

    deleted = admin_client.delete(f"/api/v1/devices/{device_id}")
    assert deleted.status_code == 204
    assert admin_client.get("/api/v1/devices").json() == []


def test_viewer_cannot_change_inventory(viewer_client):
    response = viewer_client.post("/api/v1/devices", json=DEVICE)
    assert response.status_code == 403


def test_duplicate_device_name_is_rejected(admin_client):
    assert admin_client.post("/api/v1/devices", json=DEVICE).status_code == 201
    response = admin_client.post("/api/v1/devices", json=DEVICE)
    assert response.status_code == 409


def test_http_discovery_exposes_active_devices_only(admin_client):
    assert admin_client.post("/api/v1/devices", json=DEVICE).status_code == 201
    inactive = {**DEVICE, "name": "Server Nonaktif", "is_active": False}
    assert admin_client.post("/api/v1/devices", json=inactive).status_code == 201

    response = admin_client.get("/internal/prometheus/discovery/node")
    assert response.status_code == 200
    assert response.json() == [
        {
            "targets": ["10.10.0.12:9100"],
            "labels": {
                "device_id": "1",
                "device_name": "Server Aplikasi",
                "location": "Ruang Server",
            },
        }
    ]
