from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Device, DeviceKind, NetworkLink, NetworkRole, User, UserRole, utcnow
from app.security import hash_password

DEMO_DEVICE_SPECS = (
    {
        "name": "Router Utama",
        "kind": DeviceKind.ROUTER.value,
        "address": "192.168.1.1",
        "location": "Ruang Server",
        "prometheus_job": "icmp",
        "prometheus_target": "192.168.1.1",
        "network_role": NetworkRole.GATEWAY.value,
        "asset_tag": "RT-RS-01",
        "physical_group": "Rack 01",
        "notes": "Gateway LAN contoh. Tambahkan kredensial SNMP untuk discovery port dan LLDP/CDP.",
    },
    {
        "name": "Hub Utama",
        "kind": DeviceKind.HUB.value,
        "address": "Tidak ada IP (unmanaged)",
        "location": "Ruang Server",
        "prometheus_job": "none",
        "prometheus_target": "not-monitored",
        "monitoring_level": "limited",
        "network_role": NetworkRole.DISTRIBUTION.value,
        "asset_tag": "HB-RS-01",
        "physical_group": "Rack 01",
        "notes": "Hub unmanaged tidak memiliki alamat IP dan tidak dapat melaporkan kondisi port.",
    },
    {
        "name": "Access Point",
        "kind": DeviceKind.ACCESS_POINT.value,
        "address": "192.168.1.2",
        "location": "Ruang Server",
        "prometheus_job": "icmp",
        "prometheus_target": "192.168.1.2",
        "network_role": NetworkRole.ACCESS.value,
        "asset_tag": "AP-RS-01",
        "notes": "Alamat manajemen access point contoh. Tambahkan kredensial SNMP bila tersedia.",
    },
    {
        "name": "Server Monitoring",
        "kind": DeviceKind.LINUX_SERVER.value,
        "address": "192.168.1.10",
        "location": "Ruang Server",
        "prometheus_job": "node",
        "prometheus_target": "node-exporter:9100",
        "network_role": NetworkRole.ENDPOINT.value,
        "asset_tag": "SRV-RS-01",
        "physical_group": "Rack 01",
        "notes": "Komputer 1 sebagai server monitoring. Jalankan node_exporter pada komputer ini.",
    },
    {
        "name": "Komputer 2",
        "kind": DeviceKind.OTHER.value,
        "address": "192.168.1.20",
        "location": "Ruang Kerja",
        "prometheus_job": "icmp",
        "prometheus_target": "192.168.1.20",
        "network_role": NetworkRole.ENDPOINT.value,
        "asset_tag": "PC-RK-02",
        "notes": "Komputer client contoh yang diperiksa melalui ICMP dari server monitoring.",
    },
)

DEMO_LINKS = (
    ("Router Utama", "Hub Utama"),
    ("Hub Utama", "Server Monitoring"),
    ("Hub Utama", "Komputer 2"),
    ("Hub Utama", "Access Point"),
)


def demo_link_key(local_name: str, remote_name: str) -> str:
    return f"demo:{local_name.lower().replace(' ', '-')}-{remote_name.lower().replace(' ', '-')}"


def seed_demo_network(db: Session, *, upgrade_legacy_server: bool = False) -> None:
    existing_devices = {device.name: device for device in db.scalars(select(Device))}
    devices: dict[str, Device] = {}
    for spec in DEMO_DEVICE_SPECS:
        device = existing_devices.get(spec["name"])
        if device is None:
            device = Device(**spec)
            db.add(device)
        elif (
            upgrade_legacy_server
            and device.name == "Server Monitoring"
            and device.address == "Host Linux"
        ):
            for key, value in spec.items():
                setattr(device, key, value)
        devices[device.name] = device
    db.flush()

    now = utcnow()
    existing_link_keys = {link.source_key for link in db.scalars(select(NetworkLink))}
    db.add_all(
        NetworkLink(
            source_key=demo_link_key(local_name, remote_name),
            origin="manual",
            local_device_id=devices[local_name].id,
            remote_device_id=devices[remote_name].id,
            active=True,
            last_seen_at=now,
        )
        for local_name, remote_name in DEMO_LINKS
        if demo_link_key(local_name, remote_name) not in existing_link_keys
    )


def has_legacy_demo_server(db: Session) -> bool:
    devices = list(db.scalars(select(Device)))
    return (
        len(devices) == 1
        and devices[0].name == "Server Monitoring"
        and devices[0].address == "Host Linux"
        and db.scalar(select(func.count()).select_from(NetworkLink)) == 0
    )


def bootstrap() -> None:
    if settings.app_env == "production":
        if settings.app_secret_key == "development-secret-change-before-production":
            raise RuntimeError("APP_SECRET_KEY wajib diganti untuk production")
        if settings.admin_password == "admin12345":
            raise RuntimeError("ADMIN_PASSWORD wajib diganti untuk production")
        if settings.credential_encryption_key in {
            "",
            "development-credential-key-change-me",
        }:
            raise RuntimeError("CREDENTIAL_ENCRYPTION_KEY wajib diisi untuk production")
        if settings.credential_encryption_key == settings.app_secret_key:
            raise RuntimeError("CREDENTIAL_ENCRYPTION_KEY harus berbeda dari APP_SECRET_KEY")
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(User)) == 0:
            db.add(
                User(
                    username=settings.admin_username,
                    full_name=settings.admin_full_name,
                    password_hash=hash_password(settings.admin_password),
                    role=UserRole.ADMIN.value,
                )
            )

        if settings.seed_demo_data and db.scalar(select(func.count()).select_from(Device)) == 0:
            seed_demo_network(db)
        elif settings.seed_demo_data and has_legacy_demo_server(db):
            seed_demo_network(db, upgrade_legacy_server=True)
        db.commit()


if __name__ == "__main__":
    bootstrap()
