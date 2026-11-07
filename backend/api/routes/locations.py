from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db, require_admin
from models.location import Location
from models.user import User
from schemas.location import FloorplanRead, LocationCreate, LocationRead, LocationUpdate
from services.location import (
    MAX_FLOORPLAN_BYTES,
    get_floorplan_or_404,
    get_location_devices,
)
from services.location import (
    create_location as create_location_svc,
)
from services.location import (
    delete_location as delete_location_svc,
)
from services.location import (
    list_floorplans as list_floorplans_svc,
)
from services.location import (
    list_locations as list_locations_svc,
)
from services.location import (
    update_location as update_location_svc,
)
from services.location import (
    upload_floorplan as upload_floorplan_svc,
)

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[LocationRead])
def list_locations(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Location]:
    return list_locations_svc(db)


@router.post("", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
def create_location(
    payload: LocationCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Location:
    return create_location_svc(payload, db)


@router.patch("/{location_id}", response_model=LocationRead)
def update_location(
    location_id: int,
    payload: LocationUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Location:
    return update_location_svc(location_id, payload, db)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Response:
    delete_location_svc(location_id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/floorplans", response_model=list[FloorplanRead])
def list_floorplans(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[FloorplanRead]:
    return list_floorplans_svc(db)


@router.post(
    "/{location_id}/floorplan",
    response_model=FloorplanRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_floorplan(
    location_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    file: UploadFile = File(),
) -> FloorplanRead:
    content = await file.read(MAX_FLOORPLAN_BYTES + 1)
    return upload_floorplan_svc(location_id, file.filename, file.content_type, content, db)


@router.get("/floorplans/{floorplan_id}/image", response_class=Response)
def floorplan_image(
    floorplan_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Response:
    floorplan = get_floorplan_or_404(floorplan_id, db)
    return Response(
        content=floorplan.image_data,
        media_type=floorplan.content_type,
        headers={"Cache-Control": "private, max-age=60"},
    )


@router.get("/{location_id}/devices")
def location_devices(
    location_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    return get_location_devices(location_id, db)
