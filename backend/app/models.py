from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class UserRole(StrEnum):
    ADMIN = "admin"
    VIEWER = "viewer"


class DeviceKind(StrEnum):
    LINUX_SERVER = "linux_server"
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


class LocationKind(StrEnum):
    SITE = "site"
    BUILDING = "building"
    FLOOR = "floor"
    ROOM = "room"


class CredentialKind(StrEnum):
    SNMP_V2C = "snmp_v2c"
    SNMP_V3 = "snmp_v3"
    ONVIF_RTSP = "onvif_rtsp"


class PortExpectationMode(StrEnum):
    REQUIRED = "required"
    SPARE = "spare"
    IGNORED = "ignored"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=UserRole.VIEWER.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint("parent_id", "name", name="uq_location_parent_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    address: Mapped[str] = mapped_column(String(255), default="")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    parent: Mapped["Location | None"] = relationship(
        "Location", remote_side="Location.id", back_populates="children"
    )
    children: Mapped[list["Location"]] = relationship(
        "Location", back_populates="parent", cascade="all, delete-orphan"
    )


class Floorplan(Base):
    __tablename__ = "floorplans"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), unique=True, index=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(80))
    image_data: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class CredentialProfile(Base):
    __tablename__ = "credential_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(24))
    encrypted_payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


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
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class NetworkPort(Base):
    __tablename__ = "network_ports"
    __table_args__ = (
        UniqueConstraint("device_id", "source_port_id", name="uq_network_port_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    source_port_id: Mapped[int] = mapped_column(Integer)
    if_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(String(255), default="")
    alias: Mapped[str] = mapped_column(String(255), default="")
    admin_status: Mapped[str] = mapped_column(String(20), default="unknown")
    oper_status: Mapped[str] = mapped_column(String(20), default="unknown")
    speed_bps: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    rx_bps: Mapped[float | None] = mapped_column(Float, nullable=True)
    tx_bps: Mapped[float | None] = mapped_column(Float, nullable=True)
    errors_in: Mapped[float | None] = mapped_column(Float, nullable=True)
    errors_out: Mapped[float | None] = mapped_column(Float, nullable=True)
    discards_in: Mapped[float | None] = mapped_column(Float, nullable=True)
    discards_out: Mapped[float | None] = mapped_column(Float, nullable=True)
    mac_address: Mapped[str] = mapped_column(String(40), default="")
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PortExpectation(Base):
    __tablename__ = "port_expectations"

    id: Mapped[int] = mapped_column(primary_key=True)
    port_id: Mapped[int] = mapped_column(
        ForeignKey("network_ports.id", ondelete="CASCADE"), unique=True, index=True
    )
    mode: Mapped[str] = mapped_column(String(20), default=PortExpectationMode.SPARE.value)
    expected_device_id: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id", ondelete="SET NULL"), nullable=True
    )
    label: Mapped[str] = mapped_column(String(160), default="")
    consecutive_mismatches: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class NetworkLink(Base):
    __tablename__ = "network_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    origin: Mapped[str] = mapped_column(String(20))
    local_device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )
    local_port_id: Mapped[int | None] = mapped_column(
        ForeignKey("network_ports.id", ondelete="SET NULL"), nullable=True
    )
    remote_device_id: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), nullable=True, index=True
    )
    remote_port_id: Mapped[int | None] = mapped_column(
        ForeignKey("network_ports.id", ondelete="SET NULL"), nullable=True
    )
    remote_name: Mapped[str] = mapped_column(String(255), default="")
    remote_port_name: Mapped[str] = mapped_column(String(160), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DeviceObservation(Base):
    __tablename__ = "device_observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), unique=True, index=True
    )
    source: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(20), default="unknown")
    reason: Mapped[str] = mapped_column(String(255), default="")
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    stream_status: Mapped[str | None] = mapped_column(String(24), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
