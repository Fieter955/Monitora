from core.config import settings
from schemas.system import SystemCapabilities


def get_system_capabilities() -> SystemCapabilities:
    profile = "windows_native" if settings.native_windows else "docker_full"
    return SystemCapabilities(
        deployment_profile=profile,
        librenms=settings.enable_librenms and not settings.native_windows,
        vmware=settings.enable_vmware,
        advanced_topology=settings.enable_advanced_topology and not settings.native_windows,
    )
