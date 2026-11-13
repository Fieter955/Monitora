from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db, require_admin
from models.credential import CredentialProfile
from models.device import Device
from models.user import User
from schemas.credential import CredentialProfileRead
from schemas.device import BulkPlacementUpdate, DeviceCreate, DeviceRead, DeviceUpdate
from services.device import (
    bulk_place_devices,
    get_device_or_404,
    list_credential_profiles,
)
from services.device import (
    create_device as create_device_svc,
)
from services.device import (
    delete_device as delete_device_svc,
)
from services.device import (
    list_devices as list_devices_svc,
)
from services.device import (
    update_device as update_device_svc,
)

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceRead])
def list_devices(
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Device]:
    return list_devices_svc(db)[offset : offset + limit]


@router.patch("/bulk-placement", response_model=list[DeviceRead])
def bulk_place_devices_api(
    payload: BulkPlacementUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[Device]:
    return bulk_place_devices(payload, db)


@router.get("/credentials/profiles", response_model=list[CredentialProfileRead])
def list_credentials(
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[CredentialProfile]:
    return list_credential_profiles(db)[offset : offset + limit]


@router.post("", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
def create_device(
    payload: DeviceCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Device:
    return create_device_svc(payload, db)


@router.get("/{device_id}", response_model=DeviceRead)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Device:
    return get_device_or_404(device_id, db)


@router.patch("/{device_id}", response_model=DeviceRead)
def update_device(
    device_id: int,
    payload: DeviceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Device:
    return update_device_svc(device_id, payload, db)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Response:
    delete_device_svc(device_id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
