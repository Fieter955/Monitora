from datetime import datetime
from typing import Self
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from models.device import DeviceKind, NetworkRole
from schemas.credential import CredentialSecret


def validate_stream_url(value: str) -> str:
    if not value:
        return value
    if any(char in value for char in ("\r", "\n", " ", "\t")):
        raise ValueError("URL stream tidak boleh memuat spasi atau karakter baris baru")
    parsed = urlparse(value)
    if parsed.scheme.lower() != "rtsp" or not parsed.hostname:
        raise ValueError("URL stream harus memakai skema rtsp:// yang valid")
    if parsed.username or parsed.password:
        raise ValueError(
            "Jangan masukkan kredensial ke URL stream; gunakan kolom username/password"
        )
    return value


class DeviceBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    kind: DeviceKind
    address: str = Field(min_length=2, max_length=255)
    location: str = Field(default="", max_length=160)
    prometheus_job: str = Field(min_length=1, max_length=80)
    prometheus_target: str = Field(min_length=1, max_length=255)
    notes: str = Field(default="", max_length=2000)
    is_active: bool = True
    room_id: int | None = None
    credential_profile_id: int | None = None
    stream_url: str = Field(default="", max_length=2000)
    floorplan_x: float | None = Field(default=None, ge=0, le=100)
    floorplan_y: float | None = Field(default=None, ge=0, le=100)
    asset_tag: str | None = Field(default=None, max_length=80)
    physical_group: str = Field(default="", max_length=160)
    physical_position: str = Field(default="", max_length=160)
    network_role: NetworkRole = NetworkRole.ENDPOINT
    isp_name: str = Field(default="", max_length=160)
    wan_if_name: str = Field(default="", max_length=160)
    wan_if_index: int | None = Field(default=None, ge=1)

    @field_validator("name", "address", "prometheus_job", "prometheus_target")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Nilai tidak boleh kosong")
        if any(c in value for c in ("\r", "\n")):
            raise ValueError("Nilai tidak boleh memuat karakter baris baru")
        return value

    @field_validator("stream_url")
    @classmethod
    def reject_embedded_stream_credentials(cls, value: str) -> str:
        return validate_stream_url(value)

    @field_validator("asset_tag")
    @classmethod
    def normalize_asset_tag(cls, value: str | None) -> str | None:
        return value.strip().upper() or None if value is not None else None

    @model_validator(mode="after")
    def require_cctv_stream(self) -> Self:
        if self.kind == DeviceKind.CCTV and not self.stream_url.strip():
            raise ValueError("CCTV memerlukan URL stream RTSP")
        return self


class DeviceCreate(DeviceBase):
    model_config = ConfigDict(extra="forbid")

    credential: CredentialSecret | None = None


class DeviceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=160)
    kind: DeviceKind | None = None
    address: str | None = Field(default=None, min_length=2, max_length=255)
    location: str | None = Field(default=None, max_length=160)
    prometheus_job: str | None = Field(default=None, min_length=1, max_length=80)
    prometheus_target: str | None = Field(default=None, min_length=1, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None
    room_id: int | None = None
    credential_profile_id: int | None = None
    credential: CredentialSecret | None = None
    stream_url: str | None = Field(default=None, max_length=2000)
    floorplan_x: float | None = Field(default=None, ge=0, le=100)
    floorplan_y: float | None = Field(default=None, ge=0, le=100)
    asset_tag: str | None = Field(default=None, max_length=80)
    physical_group: str | None = Field(default=None, max_length=160)
    physical_position: str | None = Field(default=None, max_length=160)
    network_role: NetworkRole | None = None
    isp_name: str | None = Field(default=None, max_length=160)
    wan_if_name: str | None = Field(default=None, max_length=160)
    wan_if_index: int | None = Field(default=None, ge=1)

    @field_validator("name", "address", "prometheus_job", "prometheus_target")
    @classmethod
    def strip_optional_required(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Nilai tidak boleh kosong")
        if any(c in value for c in ("\r", "\n")):
            raise ValueError("Nilai tidak boleh memuat karakter baris baru")
        return value

    @field_validator("stream_url")
    @classmethod
    def reject_embedded_stream_credentials(cls, value: str | None) -> str | None:
        return validate_stream_url(value) if value is not None else None

    @field_validator("asset_tag")
    @classmethod
    def normalize_asset_tag(cls, value: str | None) -> str | None:
        return value.strip().upper() or None if value is not None else None


class DeviceRead(DeviceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    librenms_device_id: int | None
    capabilities: dict
    monitoring_level: str
    last_seen_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class BulkPlacementUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_ids: list[int] = Field(min_length=1, max_length=100)
    room_id: int
    floorplan_x: float = Field(ge=0, le=100)
    floorplan_y: float = Field(ge=0, le=100)
    physical_group: str = Field(default="", max_length=160)
