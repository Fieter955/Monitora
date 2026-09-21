from fastapi import APIRouter
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession
from app.models import Device, Location
from app.network_service import device_health
from app.prometheus import prometheus_client
from app.routers.network import combine_reachability
from app.schemas import ProblemLocatorRead

router = APIRouter(prefix="/operations", tags=["operations"])


def location_path(room_id: int | None, locations: dict[int, Location]) -> list[str]:
    result: list[str] = []
    current_id = room_id
    visited: set[int] = set()
    while current_id is not None and current_id not in visited:
        visited.add(current_id)
        location = locations.get(current_id)
        if location is None:
            break
        result.append(location.name)
        current_id = location.parent_id
    result.reverse()
    return result


@router.get("/problems", response_model=list[ProblemLocatorRead])
def list_problems(db: DbSession, _: CurrentUser) -> list[ProblemLocatorRead]:
    devices = list(
        db.scalars(
            select(Device).where(Device.archived_at.is_(None), Device.is_active.is_(True))
        )
    )
    locations = {item.id: item for item in db.scalars(select(Location))}
    summary = prometheus_client.summary(devices)
    metric_status = {item.device_id: item.status for item in summary.devices}
    problems: list[ProblemLocatorRead] = []
    for device in devices:
        health = combine_reachability(device_health(device, db), metric_status.get(device.id))
        if health.status not in {"critical", "warning"}:
            continue
        problems.append(
            ProblemLocatorRead(
                device_id=device.id,
                name=device.name,
                kind=device.kind,
                address=device.address,
                status=health.status,
                issues=health.issues,
                room_id=device.room_id,
                location_path=location_path(device.room_id, locations),
                asset_tag=device.asset_tag,
                physical_group=device.physical_group,
                physical_position=device.physical_position,
                floorplan_x=device.floorplan_x,
                floorplan_y=device.floorplan_y,
                last_seen_at=health.last_seen_at,
            )
        )
    priority = {"critical": 0, "warning": 1}
    return sorted(
        problems,
        key=lambda item: (
            priority[item.status],
            "/".join(item.location_path).casefold(),
            item.name.casefold(),
        ),
    )
