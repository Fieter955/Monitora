from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from models.device import DeviceKind, NetworkRole
from models.network import PortExpectationMode
from schemas.credential import CredentialSecret
from schemas.device import validate_stream_url


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


class ManualLinkCreate(BaseModel):
    local_device_id: int
    local_port_id: int | None = None
    remote_device_id: int
    remote_port_id: int | None = None
