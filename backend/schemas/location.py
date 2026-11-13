from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.location import LocationKind


class LocationBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    kind: LocationKind
    parent_id: int | None = None
    sort_order: int = 0
    address: str = Field(default="", max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class LocationCreate(LocationBase):
    model_config = ConfigDict(extra="forbid")


class LocationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=160)
    parent_id: int | None = None
    sort_order: int | None = None
    address: str | None = Field(default=None, max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class LocationRead(LocationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class FloorplanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location_id: int
    filename: str
    content_type: str
    image_url: str
    updated_at: datetime


class LocationDeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    kind: str
    address: str
    floorplan_x: float | None
    floorplan_y: float | None
    monitoring_level: str
