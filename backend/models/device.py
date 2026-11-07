from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from db.base import Base
from models.user import utcnow


class DeviceKind(StrEnum):
    LINUX_SERVER = "linux_server"
    WINDOWS_SERVER = "windows_server"
    ROUTER = "router"
    SWITCH = "switch"
    ACCESS_POINT = "access_point"
    CCTV = "cctv"
    HUB = "hub"
    WEBSITE = "website"
    OTHER = "other"


class NetworkRole(StrEnum):
    GATEWAY = "gateway"
    DISTRIBUTION = "distribution"
    ACCESS = "access"
    ENDPOINT = "endpoint"


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(32))
    address: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(160), default="")
    prometheus_job: Mapped[str] = mapped_column(String(80))
    prometheus_target: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    room_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    credential_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("credential_profiles.id", ondelete="SET NULL"), nullable=True
    )
    librenms_device_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    capabilities: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=dict
    )
    monitoring_level: Mapped[str] = mapped_column(String(20), default="basic")
    stream_url: Mapped[str] = mapped_column(Text, default="")
    floorplan_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    floorplan_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    asset_tag: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True)
    physical_group: Mapped[str] = mapped_column(String(160), default="")
    physical_position: Mapped[str] = mapped_column(String(160), default="")
    network_role: Mapped[str] = mapped_column(String(24), default=NetworkRole.ENDPOINT.value)
    isp_name: Mapped[str] = mapped_column(String(160), default="")
    wan_if_name: Mapped[str] = mapped_column(String(160), default="")
    wan_if_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
