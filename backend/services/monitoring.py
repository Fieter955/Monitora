from sqlalchemy import select
from sqlalchemy.orm import Session

from models.device import Device, DeviceKind
from schemas.monitoring import AlertRead, MonitoringSummary
from services.prometheus import prometheus_client


def get_monitoring_summary(db: Session) -> MonitoringSummary:
    query = (
        select(Device)
        .where(Device.is_active.is_(True), Device.archived_at.is_(None))
        .order_by(Device.name)
    )
    devices = list(db.scalars(query))
    return prometheus_client.summary(devices)


def get_alerts(state: str | None = None) -> list[AlertRead]:
    try:
        results = prometheus_client.alerts()
    except Exception:
        return []
    return [item for item in results if state is None or item.state == state]


def get_discovery_targets(
    db: Session, kinds: set[str], job: str, *, include_network_role: bool = False
) -> list[dict]:
    devices = list(
        db.scalars(
            select(Device)
            .where(
                Device.is_active.is_(True),
                Device.archived_at.is_(None),
                Device.kind.in_(kinds),
                Device.prometheus_job == job,
            )
            .order_by(Device.name)
        )
    )
    results = []
    for device in devices:
        labels = {
            "device_id": str(device.id),
            "device_name": device.name,
            "location": device.location or "-",
        }
        if include_network_role:
            labels["network_role"] = device.network_role
        results.append({
            "targets": [device.prometheus_target],
            "labels": labels,
        })
    return results


def get_node_discovery(db: Session) -> list[dict]:
    return get_discovery_targets(db, {DeviceKind.LINUX_SERVER.value}, "node")


def get_windows_discovery(db: Session) -> list[dict]:
    return get_discovery_targets(db, {DeviceKind.WINDOWS_SERVER.value}, "windows")


def get_blackbox_discovery(db: Session) -> list[dict]:
    return get_discovery_targets(db, {DeviceKind.WEBSITE.value}, "blackbox")


def get_icmp_discovery(db: Session) -> list[dict]:
    return get_discovery_targets(
        db,
        {
            DeviceKind.ROUTER.value,
            DeviceKind.SWITCH.value,
            DeviceKind.ACCESS_POINT.value,
            DeviceKind.OTHER.value,
        },
        "icmp",
    )


def get_snmp_discovery(db: Session) -> list[dict]:
    return get_discovery_targets(
        db,
        {
            DeviceKind.ROUTER.value,
            DeviceKind.SWITCH.value,
            DeviceKind.ACCESS_POINT.value,
        },
        "snmp",
        include_network_role=True,
    )


def get_gateway_discovery(db: Session) -> list[dict]:
    devices = list(
        db.scalars(
            select(Device)
            .where(
                Device.is_active.is_(True),
                Device.archived_at.is_(None),
                Device.kind == DeviceKind.ROUTER.value,
                Device.network_role == "gateway",
            )
            .order_by(Device.name)
        )
    )
    return [
        {
            "targets": [device.address],
            "labels": {
                "device_id": str(device.id),
                "device_name": device.name,
                "location": device.location or "-",
                "network_role": device.network_role,
            },
        }
        for device in devices
    ]
