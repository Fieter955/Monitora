from fastapi import APIRouter, Query
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession
from app.models import Device, DeviceKind
from app.prometheus import prometheus_client
from app.schemas import AlertRead, MonitoringSummary

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/summary", response_model=MonitoringSummary)
def summary(db: DbSession, _: CurrentUser) -> MonitoringSummary:
    query = (
        select(Device)
        .where(Device.is_active.is_(True), Device.archived_at.is_(None))
        .order_by(Device.name)
    )
    devices = list(db.scalars(query))
    return prometheus_client.summary(devices)


@router.get("/alerts", response_model=list[AlertRead])
def alerts(
    _: CurrentUser,
    state: str | None = Query(default=None, pattern="^(pending|firing)$"),
) -> list[AlertRead]:
    try:
        results = prometheus_client.alerts()
    except Exception:
        return []
    return [item for item in results if state is None or item.state == state]


def discovery_targets(db: DbSession, kinds: set[str], job: str) -> list[dict]:
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
    return [
        {
            "targets": [device.prometheus_target],
            "labels": {
                "device_id": str(device.id),
                "device_name": device.name,
                "location": device.location or "-",
            },
        }
        for device in devices
    ]


def node_discovery(db: DbSession) -> list[dict]:
    return discovery_targets(db, {DeviceKind.LINUX_SERVER.value}, "node")


def blackbox_discovery(db: DbSession) -> list[dict]:
    return discovery_targets(db, {DeviceKind.WEBSITE.value}, "blackbox")


def icmp_discovery(db: DbSession) -> list[dict]:
    return discovery_targets(
        db,
        {
            DeviceKind.ROUTER.value,
            DeviceKind.SWITCH.value,
            DeviceKind.ACCESS_POINT.value,
            DeviceKind.OTHER.value,
        },
        "icmp",
    )


def snmp_discovery(db: DbSession) -> list[dict]:
    return discovery_targets(
        db,
        {
            DeviceKind.ROUTER.value,
            DeviceKind.SWITCH.value,
            DeviceKind.ACCESS_POINT.value,
        },
        "snmp",
    )
