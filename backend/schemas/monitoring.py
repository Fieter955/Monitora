from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class DeviceMetric(BaseModel):
    device_id: int
    status: str
    cpu_percent: float | None = None
    memory_percent: float | None = None
    disk_percent: float | None = None
    uptime_seconds: float | None = None
    receive_bytes_per_second: float | None = None
    transmit_bytes_per_second: float | None = None


class InternetHealth(BaseModel):
    status: Literal["healthy", "warning", "critical", "unknown"]
    cause: Literal["none", "lan_or_router", "wan_link", "isp_upstream", "dns", "https", "unknown"]
    summary: str
    gateway_device_id: int | None = None
    gateway_reachable: bool | None = None
    wan_oper_up: bool | None = None
    internet_ip_reachable: bool | None = None
    dns_reachable: bool | None = None
    https_reachable: bool | None = None
    checked_at: datetime


class MonitoringSummary(BaseModel):
    available: bool
    checked_at: datetime
    total_devices: int
    online_devices: int
    offline_devices: int
    unknown_devices: int
    firing_alerts: int
    devices: list[DeviceMetric]
    internet_health: InternetHealth | None = None
    message: str | None = None


class SnmpInterfaceRead(BaseModel):
    if_index: int
    if_name: str
    if_description: str = ""
    if_alias: str = ""
    oper_up: bool | None = None


class AlertRead(BaseModel):
    name: str
    severity: str
    state: str
    instance: str
    summary: str
    active_since: datetime | None = None
    device_id: int | None = None
