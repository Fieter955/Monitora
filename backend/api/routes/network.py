from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db, require_admin
from models.user import User
from schemas.monitoring import SnmpInterfaceRead
from schemas.network import (
    ConnectionTestRequest,
    ConnectionTestResult,
    DeviceHealthRead,
    DiscoveryResult,
    ManualLinkCreate,
    PortExpectationsUpdate,
    TopologyRead,
)
from services.network import (
    create_manual_link as create_manual_link_svc,
)
from services.network import (
    discover_device as discover_device_svc,
)
from services.network import (
    get_device_health as get_device_health_svc,
)
from services.network import (
    get_discovery_state,
    get_internal_metrics,
    get_snmp_interfaces,
    get_topology,
)
from services.network import (
    sync_network as sync_network_svc,
)
from services.network import (
    test_connection as test_connection_svc,
)
from services.network import (
    update_port_expectations as update_port_expectations_svc,
)

router = APIRouter(tags=["network visibility"])
internal_router = APIRouter(
    prefix="/internal/prometheus", tags=["internal"], include_in_schema=False
)


@router.post(
    "/devices/test-connection",
    response_model=ConnectionTestResult,
    status_code=status.HTTP_200_OK,
)
def test_connection(
    payload: ConnectionTestRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> ConnectionTestResult:
    return test_connection_svc(payload, db)


@router.post(
    "/devices/{device_id}/discover",
    response_model=DiscoveryResult,
    status_code=status.HTTP_200_OK,
)
def discover_device(
    device_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> DiscoveryResult:
    return discover_device_svc(device_id, db)


@router.get(
    "/devices/{device_id}/snmp-interfaces",
    response_model=list[SnmpInterfaceRead],
)
def snmp_interfaces(
    device_id: int,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[SnmpInterfaceRead]:
    return get_snmp_interfaces(device_id, db)[offset : offset + limit]


@router.get("/devices/{device_id}/discovery", response_model=DiscoveryResult)
def discovery_state(
    device_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DiscoveryResult:
    return get_discovery_state(device_id, db)


@router.put("/devices/{device_id}/port-expectations", response_model=DeviceHealthRead)
def update_port_expectations(
    device_id: int,
    payload: PortExpectationsUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> DeviceHealthRead:
    return update_port_expectations_svc(device_id, payload, db)


@router.get("/devices/{device_id}/health", response_model=DeviceHealthRead)
def get_device_health(
    device_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DeviceHealthRead:
    return get_device_health_svc(device_id, db)


@router.post(
    "/topology/links/manual",
    response_model=TopologyRead,
    status_code=status.HTTP_200_OK,
)
def create_manual_link(
    payload: ManualLinkCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> TopologyRead:
    create_manual_link_svc(payload, db)
    return get_topology(db)


@router.get("/topology", response_model=TopologyRead)
def topology(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    room_id: int | None = None,
    focus_device_id: int | None = None,
    scope: Literal["all", "neighbors", "path"] = "all",
) -> TopologyRead:
    return get_topology(db, room_id, focus_device_id, scope)


@router.post(
    "/network/sync",
    response_model=TopologyRead,
    status_code=status.HTTP_200_OK,
)
def sync_network(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> TopologyRead:
    return sync_network_svc(db)


@internal_router.get("/network-metrics")
def internal_metrics(db: Session = Depends(get_db)) -> PlainTextResponse:
    lines = get_internal_metrics(db)
    return PlainTextResponse(lines)
