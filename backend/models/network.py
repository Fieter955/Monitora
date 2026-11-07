from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from models.user import utcnow


class PortExpectationMode(StrEnum):
    REQUIRED = "required"
    SPARE = "spare"
    IGNORED = "ignored"


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
