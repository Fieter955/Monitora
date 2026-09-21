from sqlalchemy import select

from app.bootstrap import bootstrap
from app.config import settings
from app.database import SessionLocal
from app.models import Device, DeviceKind, NetworkLink


def test_bootstrap_seeds_simple_lan_and_is_idempotent(monkeypatch):
    monkeypatch.setattr(settings, "seed_demo_data", True)
    bootstrap()

    with SessionLocal() as db:
        devices = list(db.scalars(select(Device)))
        links = list(db.scalars(select(NetworkLink)))

        assert {device.name for device in devices} == {
            "Router Utama",
            "Hub Utama",
            "Access Point",
            "Server Monitoring",
            "Komputer 2",
        }
        assert len(links) == 4
        assert {link.origin for link in links} == {"manual"}

    bootstrap()

    with SessionLocal() as db:
        assert db.scalar(select(Device).where(Device.name == "Router Utama")) is not None
        assert len(list(db.scalars(select(Device)))) == 5
        assert len(list(db.scalars(select(NetworkLink)))) == 4


def test_bootstrap_upgrades_the_previous_single_server_seed(monkeypatch):
    monkeypatch.setattr(settings, "seed_demo_data", True)
    with SessionLocal() as db:
        db.add(
            Device(
                name="Server Monitoring",
                kind=DeviceKind.LINUX_SERVER.value,
                address="Host Linux",
                location="Ruang Server",
                prometheus_job="node",
                prometheus_target="node-exporter:9100",
            )
        )
        db.commit()

    bootstrap()

    with SessionLocal() as db:
        devices = list(db.scalars(select(Device)))
        assert len(devices) == 5
        server = db.scalar(select(Device).where(Device.name == "Server Monitoring"))
        assert server is not None
        assert server.address == "192.168.1.10"
        assert len(list(db.scalars(select(NetworkLink)))) == 4


def test_bootstrap_does_not_seed_demo_devices_by_default():
    bootstrap()

    with SessionLocal() as db:
        assert list(db.scalars(select(Device))) == []
        assert list(db.scalars(select(NetworkLink))) == []
