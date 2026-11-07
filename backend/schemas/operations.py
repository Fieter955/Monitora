from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from models.device import DeviceKind
from schemas.network import DeviceIssue


class ProblemLocatorRead(BaseModel):
    device_id: int
    name: str
    kind: DeviceKind
    address: str
    status: Literal["warning", "critical"]
    issues: list[DeviceIssue]
    room_id: int | None
    location_path: list[str]
    asset_tag: str | None
    physical_group: str
    physical_position: str
    floorplan_x: float | None
    floorplan_y: float | None
    last_seen_at: datetime | None
