from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from models.user import utcnow


class LocationKind(StrEnum):
    SITE = "site"
    BUILDING = "building"
    FLOOR = "floor"
    ROOM = "room"


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
