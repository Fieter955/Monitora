from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from models.user import User
from schemas.system import HealthStatus, SystemCapabilities
from services.system import check_db_ready, get_system_capabilities

router = APIRouter(prefix="/system", tags=["system"])
internal_router = APIRouter(tags=["internal"], include_in_schema=False)


@router.get("/capabilities", response_model=SystemCapabilities)
def capabilities(_: User = Depends(get_current_user)) -> SystemCapabilities:
    return get_system_capabilities()


@internal_router.get("/ready", response_model=HealthStatus)
def ready(db: Session = Depends(get_db)) -> HealthStatus:
    return check_db_ready(db)
