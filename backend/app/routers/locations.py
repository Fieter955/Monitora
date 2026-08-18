from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.dependencies import AdminUser, CurrentUser, DbSession
from app.models import Device, Floorplan, Location, LocationKind
from app.schemas import FloorplanRead, LocationCreate, LocationRead, LocationUpdate

router = APIRouter(prefix="/locations", tags=["locations"])

PARENT_KIND = {
    LocationKind.SITE.value: None,
    LocationKind.BUILDING.value: LocationKind.SITE.value,
    LocationKind.FLOOR.value: LocationKind.BUILDING.value,
    LocationKind.ROOM.value: LocationKind.FLOOR.value,
}
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_FLOORPLAN_BYTES = 10 * 1024 * 1024


def valid_image_signature(content_type: str, content: bytes) -> bool:
    if content_type == "image/png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")
    if content_type == "image/webp":
        return content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    return False


def get_location_or_404(location_id: int, db: DbSession) -> Location:
    location = db.get(Location, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Lokasi tidak ditemukan")
    return location


def validate_parent(kind: str, parent_id: int | None, db: DbSession) -> None:
    expected = PARENT_KIND[kind]
    if expected is None:
        if parent_id is not None:
            raise HTTPException(status_code=422, detail="Site tidak boleh memiliki induk")
        return
    if parent_id is None:
        raise HTTPException(status_code=422, detail=f"{kind} harus memiliki lokasi induk")
    parent = get_location_or_404(parent_id, db)
    if parent.kind != expected:
        raise HTTPException(
            status_code=422,
            detail=f"Induk {kind} harus berjenis {expected}",
        )


@router.get("", response_model=list[LocationRead])
def list_locations(db: DbSession, _: CurrentUser) -> list[Location]:
    return list(db.scalars(select(Location).order_by(Location.sort_order, Location.name)))


@router.post("", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
def create_location(payload: LocationCreate, db: DbSession, _: AdminUser) -> Location:
    validate_parent(payload.kind.value, payload.parent_id, db)
    location = Location(**payload.model_dump(mode="json"))
    db.add(location)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Nama lokasi sudah digunakan pada induk ini"
        ) from exc
    db.refresh(location)
    return location


@router.patch("/{location_id}", response_model=LocationRead)
def update_location(
    location_id: int, payload: LocationUpdate, db: DbSession, _: AdminUser
) -> Location:
    location = get_location_or_404(location_id, db)
    values = payload.model_dump(exclude_unset=True)
    parent_id = values.get("parent_id", location.parent_id)
    validate_parent(location.kind, parent_id, db)
    if parent_id == location.id:
        raise HTTPException(status_code=422, detail="Lokasi tidak dapat menjadi induknya sendiri")
    for key, value in values.items():
        setattr(location, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Nama lokasi sudah digunakan pada induk ini"
        ) from exc
    db.refresh(location)
    return location


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(location_id: int, db: DbSession, _: AdminUser) -> Response:
    location = get_location_or_404(location_id, db)
    has_devices = db.scalar(select(Device.id).where(Device.room_id == location.id).limit(1))
    has_children = db.scalar(select(Location.id).where(Location.parent_id == location.id).limit(1))
    if has_devices or has_children:
        raise HTTPException(
            status_code=409,
            detail="Pindahkan perangkat dan hapus lokasi turunannya terlebih dahulu",
        )
    db.delete(location)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def floorplan_read(floorplan: Floorplan) -> FloorplanRead:
    return FloorplanRead(
        id=floorplan.id,
        location_id=floorplan.location_id,
        filename=floorplan.filename,
        content_type=floorplan.content_type,
        image_url=f"/api/v1/locations/floorplans/{floorplan.id}/image",
        updated_at=floorplan.updated_at,
    )


@router.get("/floorplans", response_model=list[FloorplanRead])
def list_floorplans(db: DbSession, _: CurrentUser) -> list[FloorplanRead]:
    return [floorplan_read(item) for item in db.scalars(select(Floorplan))]


@router.post(
    "/{location_id}/floorplan",
    response_model=FloorplanRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_floorplan(
    location_id: int,
    db: DbSession,
    _: AdminUser,
    file: Annotated[UploadFile, File()],
) -> FloorplanRead:
    location = get_location_or_404(location_id, db)
    if location.kind not in {LocationKind.FLOOR.value, LocationKind.ROOM.value}:
        raise HTTPException(
            status_code=422, detail="Denah hanya dapat dipasang pada lantai atau ruang"
        )
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Gunakan gambar PNG, JPG, atau WebP")
    content = await file.read(MAX_FLOORPLAN_BYTES + 1)
    if len(content) > MAX_FLOORPLAN_BYTES:
        raise HTTPException(status_code=413, detail="Ukuran denah maksimal 10 MB")
    if not content:
        raise HTTPException(status_code=422, detail="Berkas denah kosong")
    if not valid_image_signature(file.content_type, content):
        raise HTTPException(status_code=422, detail="Isi berkas tidak cocok dengan format gambar")
    floorplan = db.scalar(select(Floorplan).where(Floorplan.location_id == location_id))
    created = floorplan is None
    if floorplan is None:
        floorplan = Floorplan(location_id=location_id, filename="", content_type="", image_data=b"")
        db.add(floorplan)
    floorplan.filename = (file.filename or "denah")[:255]
    floorplan.content_type = file.content_type
    floorplan.image_data = content
    db.commit()
    db.refresh(floorplan)
    if not created:
        # The endpoint stays idempotent for the UI while preserving a clear response model.
        pass
    return floorplan_read(floorplan)


@router.get("/floorplans/{floorplan_id}/image", response_class=Response)
def floorplan_image(floorplan_id: int, db: DbSession, _: CurrentUser) -> Response:
    floorplan = db.get(Floorplan, floorplan_id)
    if floorplan is None:
        raise HTTPException(status_code=404, detail="Denah tidak ditemukan")
    return Response(
        content=floorplan.image_data,
        media_type=floorplan.content_type,
        headers={"Cache-Control": "private, max-age=60"},
    )


@router.get("/{location_id}/devices")
def location_devices(location_id: int, db: DbSession, _: CurrentUser) -> list[dict]:
    get_location_or_404(location_id, db)
    devices = list(
        db.scalars(
            select(Device)
            .where(Device.room_id == location_id, Device.archived_at.is_(None))
            .order_by(Device.name)
        )
    )
    return [
        {
            "id": device.id,
            "name": device.name,
            "kind": device.kind,
            "address": device.address,
            "floorplan_x": device.floorplan_x,
            "floorplan_y": device.floorplan_y,
            "monitoring_level": device.monitoring_level,
        }
        for device in devices
    ]
