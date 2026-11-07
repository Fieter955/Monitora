from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from models.user import User
from schemas.monitoring import AlertRead, MonitoringSummary
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
) -> list[AlertRead]:
    return get_alerts(state)


@internal_router.get("/discovery/node")
def node_discovery(db: Session = Depends(get_db)) -> list[dict]:
    return get_node_discovery(db)


@internal_router.get("/discovery/windows")
def windows_discovery(db: Session = Depends(get_db)) -> list[dict]:
    return get_windows_discovery(db)


@internal_router.get("/discovery/blackbox")
def blackbox_discovery(db: Session = Depends(get_db)) -> list[dict]:
    return get_blackbox_discovery(db)


@internal_router.get("/discovery/icmp")
def icmp_discovery(db: Session = Depends(get_db)) -> list[dict]:
    return get_icmp_discovery(db)


@internal_router.get("/discovery/gateway")
def gateway_discovery(db: Session = Depends(get_db)) -> list[dict]:
    return get_gateway_discovery(db)


@internal_router.get("/discovery/snmp")
def snmp_discovery(db: Session = Depends(get_db)) -> list[dict]:
    return get_snmp_discovery(db)
