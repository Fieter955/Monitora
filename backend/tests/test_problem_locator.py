from app.bootstrap import seed_demo_network
from app.database import SessionLocal
from app.models import Device, DeviceObservation, utcnow


def create_location_tree(client, suffix=""):
    site = client.post("/api/v1/locations", json={"name": f"Kampus{suffix}", "kind": "site"}).json()
    building = client.post(
        "/api/v1/locations",
        json={"name": f"Gedung A{suffix}", "kind": "building", "parent_id": site["id"]},
    ).json()
    floor = client.post(
        "/api/v1/locations",
        json={"name": f"Lantai 1{suffix}", "kind": "floor", "parent_id": building["id"]},
    ).json()
    room = client.post(
        "/api/v1/locations",
        json={"name": f"Ruang Server{suffix}", "kind": "room", "parent_id": floor["id"]},
    ).json()
    return site, building, floor, room


def device_payload(name, room_id, **overrides):
    payload = {
        "name": name,
        "kind": "switch",
        "address": f"10.20.0.{room_id}",
        "prometheus_job": "snmp",
        "prometheus_target": f"10.20.0.{room_id}",
        "room_id": room_id,
    }
    payload.update(overrides)
    return payload


def test_physical_metadata_and_asset_tag_are_exposed_and_unique(admin_client):
    _, _, _, room = create_location_tree(admin_client)
    payload = device_payload(
        "Switch Utama",
        room["id"],
        asset_tag=" sw-rs-01 ",
        physical_group="Rack 01",
        physical_position="U12",
        network_role="distribution",
    )
    created = admin_client.post("/api/v1/devices", json=payload)

    assert created.status_code == 201
    assert created.json()["asset_tag"] == "SW-RS-01"
    assert created.json()["physical_position"] == "U12"
    duplicate = admin_client.post(
        "/api/v1/devices", json={**payload, "name": "Switch Cadangan"}
    )
    assert duplicate.status_code == 409


def test_bulk_placement_requires_one_room(admin_client):
    _, _, _, first_room = create_location_tree(admin_client, " 1")
    _, _, _, second_room = create_location_tree(admin_client, " 2")
    first = admin_client.post(
        "/api/v1/devices", json=device_payload("Switch Satu", first_room["id"])
    ).json()
    second = admin_client.post(
        "/api/v1/devices", json=device_payload("Switch Dua", first_room["id"])
    ).json()
    other = admin_client.post(
        "/api/v1/devices", json=device_payload("Switch Lain", second_room["id"])
    ).json()

    placed = admin_client.patch(
        "/api/v1/devices/bulk-placement",
        json={
            "device_ids": [first["id"], second["id"]],
            "room_id": first_room["id"],
            "floorplan_x": 42,
            "floorplan_y": 58,
            "physical_group": "Rack 01",
        },
    )
    assert placed.status_code == 200
    assert {(item["floorplan_x"], item["physical_group"]) for item in placed.json()} == {
        (42, "Rack 01")
    }

    rejected = admin_client.patch(
        "/api/v1/devices/bulk-placement",
        json={
            "device_ids": [first["id"], other["id"]],
            "room_id": first_room["id"],
            "floorplan_x": 20,
            "floorplan_y": 20,
        },
    )
    assert rejected.status_code == 422


def test_problem_locator_orders_severity_and_builds_location_path(admin_client):
    _, _, _, room = create_location_tree(admin_client)
    critical = admin_client.post(
        "/api/v1/devices", json=device_payload("Switch Kritis", room["id"], asset_tag="SW-01")
    ).json()
    warning = admin_client.post(
        "/api/v1/devices", json=device_payload("Switch Warning", room["id"], asset_tag="SW-02")
    ).json()
    with SessionLocal() as db:
        db.add_all(
            [
                DeviceObservation(
                    device_id=critical["id"],
                    source="icmp",
                    status="offline",
                    reason="Ping gagal",
                    checked_at=utcnow(),
                ),
                DeviceObservation(
                    device_id=warning["id"],
                    source="icmp",
                    status="unknown",
                    reason="Probe sibuk",
                    checked_at=utcnow(),
                ),
            ]
        )
        db.commit()

    response = admin_client.get("/api/v1/operations/problems")
    assert response.status_code == 200
    result = response.json()
    assert [item["device_id"] for item in result] == [critical["id"], warning["id"]]
    assert result[0]["location_path"] == ["Kampus", "Gedung A", "Lantai 1", "Ruang Server"]
    assert result[0]["issues"][0]["code"] == "network_device_down"


def test_focused_topology_returns_gateway_path(admin_client):
    with SessionLocal() as db:
        seed_demo_network(db)
        db.commit()
        target = db.query(Device).filter(Device.name == "Komputer 2").one()
        target_id = target.id

    response = admin_client.get(
        f"/api/v1/topology?focus_device_id={target_id}&scope=path"
    )
    assert response.status_code == 200
    result = response.json()
    assert result["path_complete"] is True
    assert {item["name"] for item in result["nodes"]} == {
        "Router Utama",
        "Hub Utama",
        "Komputer 2",
    }
