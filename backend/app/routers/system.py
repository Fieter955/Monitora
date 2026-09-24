from fastapi import APIRouter

from app.config import settings
from app.dependencies import CurrentUser
from app.schemas import SystemCapabilities

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/capabilities", response_model=SystemCapabilities)
def capabilities(_: CurrentUser) -> SystemCapabilities:
    profile = "windows_native" if settings.native_windows else "docker_full"
    return SystemCapabilities(
        deployment_profile=profile,
        librenms=settings.enable_librenms and not settings.native_windows,
        vmware=settings.enable_vmware,
        advanced_topology=settings.enable_advanced_topology and not settings.native_windows,
    )
