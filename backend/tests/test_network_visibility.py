from sqlalchemy import select

from app.database import SessionLocal
from app.models import Device, DeviceObservation, PortExpectation, PortExpectationMode
from app.network_service import device_health, sync_all, sync_network_device
from app.probes import ProbeResult
from app.security import decrypt_credentials, encrypt_credentials


def test_location_hierarchy_and_floorplan_validation(admin_client):
    site = admin_client.post("/api/v1/locations", json={"name": "Kampus", "kind": "site"})
    assert site.status_code == 201
    building = admin_client.post(
        "/api/v1/locations",
        json={"name": "Gedung A", "kind": "building", "parent_id": site.json()["id"]},
    )
    assert building.status_code == 201
    invalid_room = admin_client.post(
        "/api/v1/locations",
        json={"name": "Ruang Salah", "kind": "room", "parent_id": site.json()["id"]},
    )
    assert invalid_room.status_code == 422
    floor = admin_client.post(
        "/api/v1/locations",
        json={
            "name": "Lantai 1",
            "kind": "floor",
            "parent_id": building.json()["id"],
        },
    )
    assert floor.status_code == 201
    invalid_floorplan = admin_client.post(
        f"/api/v1/locations/{floor.json()['id']}/floorplan",
        files={"file": ("denah.txt", b"not-an-image", "text/plain")},
    )
    assert invalid_floorplan.status_code == 415
    disguised_file = admin_client.post(
        f"/api/v1/locations/{floor.json()['id']}/floorplan",
        files={"file": ("denah.png", b"not-an-image", "image/png")},
    )
    assert disguised_file.status_code == 422
    uploaded = admin_client.post(
        f"/api/v1/locations/{floor.json()['id']}/floorplan",
        files={"file": ("denah.png", b"\x89PNG\r\n\x1a\nminimal", "image/png")},
    )
    assert uploaded.status_code == 201
    image = admin_client.get(uploaded.json()["image_url"])
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"


def test_credentials_are_encrypted_and_authenticated():
    encrypted = encrypt_credentials({"community": "rahasia", "username": "monitor"})

    assert "rahasia" not in encrypted
    assert decrypt_credentials(encrypted) == {
        "community": "rahasia",
        "username": "monitor",
    }


class FakeLibreNMS:
    configured = True

    def add_device(self, hostname, display_name, location, credentials):
        assert hostname == "10.20.0.2"
        return 72

    def get_device(self, device_id):
        assert device_id == 72
        return {
            "status": 1,
            "snmp_disable": 0,
            "os": "ios",
            "hardware": "Switch Uji",
            "serial": "ABC123",
        }

    def get_ports(self, device_id):
        return [
            {
                "port_id": 901,
                "ifIndex": 1,
                "ifName": "Gi0/1",
                "ifDescr": "GigabitEthernet0/1",
                "ifAlias": "Kamera depan",
                "ifAdminStatus": "up",
                "ifOperStatus": "down",
                "ifSpeed": 1_000_000_000,
                "ifInOctets_rate": 0,
                "ifOutOctets_rate": 0,
            },
            {
                "port_id": 902,
                "ifIndex": 2,
                "ifName": "Gi0/2",
                "ifAdminStatus": "up",
                "ifOperStatus": "up",
                "ifSpeed": 1_000_000_000,
                "ifInOctets_rate": 12_500_000,
                "ifOutOctets_rate": 2_000_000,
            },
        ]


class OfflineLibreNMS(FakeLibreNMS):
    def get_device(self, device_id):
        result = super().get_device(device_id)
        result["status"] = 0
        return result


def test_port_expectations_require_two_consecutive_mismatches():
    with SessionLocal() as db:
        device = Device(
            name="Switch Uji",
            kind="switch",
            address="10.20.0.2",
            location="Ruang Server",
            prometheus_job="snmp",
            prometheus_target="10.20.0.2",
        )
        db.add(device)
        db.commit()
        db.refresh(device)

        ports = sync_network_device(device, db, FakeLibreNMS())
        db.flush()
        db.add_all(
            [
                PortExpectation(
                    port_id=ports[0].id,
                    mode=PortExpectationMode.REQUIRED.value,
                    label="CCTV depan",
                ),
                PortExpectation(
                    port_id=ports[1].id,
                    mode=PortExpectationMode.SPARE.value,
                ),
            ]
        )
        db.commit()

        sync_network_device(device, db, FakeLibreNMS())
        db.commit()
        first = device_health(device, db)
        assert {item.condition for item in first.ports} >= {"normal_empty", "healthy"}

        sync_network_device(device, db, FakeLibreNMS())
        db.commit()
        second = device_health(device, db)
        assert {issue.code for issue in second.issues} >= {
            "required_port_down",
            "unexpected_port_active",
        }
        active_port = next(item for item in second.ports if item.name == "Gi0/2")
        assert active_port.utilization_percent == 10.0


def test_archived_device_is_hidden_from_inventory(admin_client):
    payload = {
        "name": "Switch Arsip",
        "kind": "switch",
        "address": "10.10.10.10",
        "prometheus_job": "snmp",
        "prometheus_target": "10.10.10.10",
    }
    created = admin_client.post("/api/v1/devices", json=payload)
    assert created.status_code == 201
    assert admin_client.delete(f"/api/v1/devices/{created.json()['id']}").status_code == 204
    assert admin_client.get("/api/v1/devices").json() == []

    with SessionLocal() as db:
        stored = db.scalar(select(Device).where(Device.name == "Switch Arsip"))
        assert stored is not None
        assert stored.archived_at is not None


def test_prometheus_internal_metrics_expose_port_issue(admin_client):
    response = admin_client.get("/internal/prometheus/network-metrics")

    assert response.status_code == 200
    assert "pantau_device_issue" in response.text


def test_icmp_discovery_exposes_lan_devices_but_not_unmanaged_hub(admin_client):
    from app.bootstrap import seed_demo_network

    with SessionLocal() as db:
        seed_demo_network(db)
        db.commit()

    response = admin_client.get("/internal/prometheus/discovery/icmp")

    assert response.status_code == 200
    targets = response.json()
    assert {item["targets"][0] for item in targets} == {
        "192.168.1.1",
        "192.168.1.2",
        "192.168.1.20",
    }
    assert all(item["targets"][0] != "not-monitored" for item in targets)


def test_network_devices_are_discovered_only_by_their_selected_job(admin_client):
    devices = (
        ("Router ICMP", "router", "icmp", "10.30.0.1"),
        ("Switch ICMP", "switch", "icmp", "10.30.0.2"),
        ("Router SNMP", "router", "snmp", "10.30.0.3"),
    )
    for name, kind, job, target in devices:
        response = admin_client.post(
            "/api/v1/devices",
            json={
                "name": name,
                "kind": kind,
                "address": target,
                "prometheus_job": job,
                "prometheus_target": target,
            },
        )
        assert response.status_code == 201

    icmp_targets = {
        item["targets"][0]
        for item in admin_client.get("/internal/prometheus/discovery/icmp").json()
    }
    snmp_targets = {
        item["targets"][0]
        for item in admin_client.get("/internal/prometheus/discovery/snmp").json()
    }
    assert icmp_targets == {"10.30.0.1", "10.30.0.2"}
    assert snmp_targets == {"10.30.0.3"}


def test_icmp_router_discovery_skips_librenms(admin_client):
    created = admin_client.post(
        "/api/v1/devices",
        json={
            "name": "Router Tanpa SNMP",
            "kind": "router",
            "address": "10.40.0.1",
            "prometheus_job": "icmp",
            "prometheus_target": "10.40.0.1",
        },
    )
    device_id = created.json()["id"]

    discovered = admin_client.post(f"/api/v1/devices/{device_id}/discover")

    assert discovered.status_code == 200
    assert discovered.json()["state"] == "ready"
    assert discovered.json()["capabilities"] == ["icmp"]
    assert discovered.json()["ports"] == []


def test_icmp_connection_test_uses_blackbox_probe(admin_client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.network.icmp_probe",
        lambda address: ProbeResult(True, "online", "Ping ICMP berhasil", 1.25),
    )

    response = admin_client.post(
        "/api/v1/devices/test-connection",
        json={
            "address": "10.40.0.1",
            "kind": "router",
            "prometheus_job": "icmp",
        },
    )

    assert response.status_code == 200
    assert response.json()["reachable"] is True
    assert response.json()["capabilities"] == ["icmp"]


def test_sync_all_does_not_send_icmp_router_to_librenms():
    class UnconfiguredLibreNMS:
        configured = False

        def add_device(self, *args, **kwargs):
            raise AssertionError("ICMP-only device must not be sent to LibreNMS")

    with SessionLocal() as db:
        device = Device(
            name="Router ICMP",
            kind="router",
            address="10.50.0.1",
            prometheus_job="icmp",
            prometheus_target="10.50.0.1",
        )
        db.add(device)
        db.flush()
        db.add(
            DeviceObservation(
                device_id=device.id,
                source="librenms",
                status="unknown",
                reason="Token API LibreNMS belum dikonfigurasi",
            )
        )
        db.commit()

        sync_all(db, UnconfiguredLibreNMS())
        db.refresh(device)

        assert device.monitoring_level == "basic"
        assert device.capabilities == {"icmp": True}
        assert device_health(device, db).issues == []
        assert db.scalar(
            select(DeviceObservation).where(DeviceObservation.device_id == device.id)
        ) is None


def test_network_device_down_is_critical():
    with SessionLocal() as db:
        device = Device(
            name="Switch Offline",
            kind="switch",
            address="10.20.0.2",
            location="Ruang Server",
            prometheus_job="snmp",
            prometheus_target="10.20.0.2",
        )
        db.add(device)
        db.commit()
        db.refresh(device)

        sync_network_device(device, db, OfflineLibreNMS())
        db.commit()
        health = device_health(device, db)

        assert health.status == "critical"
        assert "network_device_down" in {issue.code for issue in health.issues}


def test_rtsp_url_rejects_embedded_credentials(admin_client):
    response = admin_client.post(
        "/api/v1/devices",
        json={
            "name": "Kamera Depan",
            "kind": "cctv",
            "address": "10.30.0.5",
            "prometheus_job": "cctv",
            "prometheus_target": "10.30.0.5",
            "stream_url": "rtsp://admin:secret@10.30.0.5/live",
        },
    )

    assert response.status_code == 422
