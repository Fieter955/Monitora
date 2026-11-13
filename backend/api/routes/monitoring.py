from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from models.user import User
from schemas.monitoring import AlertRead, DiscoveryTargetGroup, MonitoringSummary
from services.monitoring import (
    get_alerts,
    get_blackbox_discovery,
    get_gateway_discovery,
    get_icmp_discovery,
    get_monitoring_summary,
    get_node_discovery,
    get_snmp_discovery,
    get_windows_discovery,
)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
internal_router = APIRouter(
    prefix="/internal/prometheus", tags=["internal"], include_in_schema=False
)


@router.get("/summary", response_model=MonitoringSummary)
def summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MonitoringSummary:
    return get_monitoring_summary(db)


@router.get("/alerts", response_model=list[AlertRead])
def alerts(
    _: User = Depends(get_current_user),
    state: str | None = Query(default=None, pattern="^(pending|firing)$"),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[AlertRead]:
    return get_alerts(state)[offset : offset + limit]


@internal_router.get("/discovery/node", response_model=list[DiscoveryTargetGroup])
def node_discovery(db: Session = Depends(get_db)) -> list[dict]:
    return get_node_discovery(db)


@internal_router.get("/discovery/windows", response_model=list[DiscoveryTargetGroup])
def windows_discovery(db: Session = Depends(get_db)) -> list[dict]:
    return get_windows_discovery(db)


@internal_router.get("/discovery/blackbox", response_model=list[DiscoveryTargetGroup])
def blackbox_discovery(db: Session = Depends(get_db)) -> list[dict]:
    return get_blackbox_discovery(db)


@internal_router.get("/discovery/icmp", response_model=list[DiscoveryTargetGroup])
def icmp_discovery(db: Session = Depends(get_db)) -> list[dict]:
    return get_icmp_discovery(db)


@internal_router.get("/discovery/gateway", response_model=list[DiscoveryTargetGroup])
def gateway_discovery(db: Session = Depends(get_db)) -> list[dict]:
    return get_gateway_discovery(db)


@internal_router.get("/discovery/snmp", response_model=list[DiscoveryTargetGroup])
def snmp_discovery(db: Session = Depends(get_db)) -> list[dict]:
    return get_snmp_discovery(db)
