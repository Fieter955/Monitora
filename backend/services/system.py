from sqlalchemy import text
from sqlalchemy.orm import Session

from core.config import settings
from core.exceptions import ServiceUnavailableError
from schemas.system import HealthStatus, SystemCapabilities


def get_system_capabilities() -> SystemCapabilities:
    profile = "windows_native" if settings.native_windows else "docker_full"
    return SystemCapabilities(
        deployment_profile=profile,
        librenms=settings.enable_librenms and not settings.native_windows,
        vmware=settings.enable_vmware,
        advanced_topology=settings.enable_advanced_topology and not settings.native_windows,
    )


def check_db_ready(db: Session) -> HealthStatus:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise ServiceUnavailableError("Database belum siap") from exc
    return HealthStatus(status="ready")
