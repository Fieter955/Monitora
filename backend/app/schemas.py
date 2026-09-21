from datetime import datetime
from typing import Literal, Self
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import (
    CredentialKind,
    DeviceKind,
    LocationKind,
    NetworkRole,
    PortExpectationMode,
    UserRole,
)


class ApiMessage(BaseModel):
    message: str


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: UserRole
    is_active: bool


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

    @field_validator("name", "address", "prometheus_job", "prometheus_target")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Nilai tidak boleh kosong")
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


class CredentialSecret(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    kind: CredentialKind
    community: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=512)
    auth_protocol: str | None = Field(default=None, max_length=30)
    privacy_protocol: str | None = Field(default=None, max_length=30)
    privacy_password: str | None = Field(default=None, max_length=512)


class DeviceCreate(DeviceBase):
    credential: CredentialSecret | None = None


class DeviceUpdate(BaseModel):
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


class CredentialProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    kind: CredentialKind
    created_at: datetime


class LocationBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    kind: LocationKind
    parent_id: int | None = None
    sort_order: int = 0
    address: str = Field(default="", max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
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


class NetworkPortRead(BaseModel):
    id: int
    device_id: int
    source_port_id: int
    if_index: int | None
    name: str
    description: str
    alias: str
    admin_status: str
    oper_status: str
    speed_bps: int | None
    rx_bps: float | None
    tx_bps: float | None
    utilization_percent: float | None
    errors_in: float | None
    errors_out: float | None
    discards_in: float | None
    discards_out: float | None
    mac_address: str
    expectation: PortExpectationMode
    expected_device_id: int | None
    expectation_label: str
    condition: str
    last_seen_at: datetime


class PortExpectationInput(BaseModel):
    port_id: int
    mode: PortExpectationMode
    expected_device_id: int | None = None
    label: str = Field(default="", max_length=160)


class PortExpectationsUpdate(BaseModel):
    ports: list[PortExpectationInput]


class ConnectionTestRequest(BaseModel):
    address: str = Field(min_length=2, max_length=255)
    kind: DeviceKind
    prometheus_job: str | None = Field(default=None, max_length=80)
    stream_url: str = Field(default="", max_length=2000)
    credential_profile_id: int | None = None
    credential: CredentialSecret | None = None

    @field_validator("stream_url")
    @classmethod
    def reject_embedded_stream_credentials(cls, value: str) -> str:
        return validate_stream_url(value)


def validate_stream_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.username or parsed.password:
        raise ValueError(
            "Jangan masukkan kredensial ke URL stream; gunakan kolom username/password"
        )
    return value


class ConnectionTestResult(BaseModel):
    reachable: bool
    provider_available: bool
    capabilities: list[str]
    message: str
    latency_ms: float | None = None


class DiscoveryResult(BaseModel):
    device_id: int
    state: Literal["ready", "partial", "unavailable", "failed"]
    message: str
    capabilities: list[str]
    ports: list[NetworkPortRead]


class DeviceIssue(BaseModel):
    code: str
    severity: Literal["warning", "critical"]
    title: str
    detail: str
    port_id: int | None = None


class DeviceHealthRead(BaseModel):
    device_id: int
    status: Literal["healthy", "warning", "critical", "unknown"]
    monitoring_level: str
    checked_at: datetime | None
    last_seen_at: datetime | None
    reason: str
    issues: list[DeviceIssue]
    ports: list[NetworkPortRead]


class TopologyNode(BaseModel):
    id: int
    name: str
    kind: DeviceKind
    address: str
    room_id: int | None
    location: str
    status: Literal["healthy", "warning", "critical", "unknown"]
    monitoring_level: str
    network_role: NetworkRole


class TopologyEdge(BaseModel):
    id: str
    origin: str
    source_device_id: int
    target_device_id: int | None
    source_port: str
    target_port: str
    target_name: str
    active: bool
    utilization_percent: float | None


class TopologyRead(BaseModel):
    generated_at: datetime
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]
    focus_device_id: int | None = None
    path_complete: bool | None = None


class BulkPlacementUpdate(BaseModel):
    device_ids: list[int] = Field(min_length=1, max_length=100)
    room_id: int
    floorplan_x: float = Field(ge=0, le=100)
    floorplan_y: float = Field(ge=0, le=100)
    physical_group: str = Field(default="", max_length=160)


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


class ManualLinkCreate(BaseModel):
    local_device_id: int
    local_port_id: int | None = None
    remote_device_id: int
    remote_port_id: int | None = None


class DeviceMetric(BaseModel):
    device_id: int
    status: str
    cpu_percent: float | None = None
    memory_percent: float | None = None
    disk_percent: float | None = None
    uptime_seconds: float | None = None
    receive_bytes_per_second: float | None = None
    transmit_bytes_per_second: float | None = None


class MonitoringSummary(BaseModel):
    available: bool
    checked_at: datetime
    total_devices: int
    online_devices: int
    offline_devices: int
    unknown_devices: int
    firing_alerts: int
    devices: list[DeviceMetric]
    message: str | None = None


class AlertRead(BaseModel):
    name: str
    severity: str
    state: str
    instance: str
    summary: str
    active_since: datetime | None = None
    device_id: int | None = None
