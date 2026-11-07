from fastapi import APIRouter, Depends

from api.deps import get_current_user
from models.user import User
from schemas.system import SystemCapabilities
from services.system import get_system_capabilities

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/capabilities", response_model=SystemCapabilities)
def capabilities(_: User = Depends(get_current_user)) -> SystemCapabilities:
    return get_system_capabilities()
