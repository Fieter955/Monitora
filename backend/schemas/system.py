from typing import Literal

from pydantic import BaseModel


class SystemCapabilities(BaseModel):
    deployment_profile: Literal["docker_full", "windows_native"]
    librenms: bool
    snmp: bool = True
    grafana: bool = True
    vmware: bool
    advanced_topology: bool
