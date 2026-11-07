from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.exceptions import (
    ConflictError,
    DuplicateDataError,
    NotFoundError,
    PayloadTooLargeError,
    UnprocessableEntityError,
    UnsupportedMediaTypeError,
)
from models.device import Device
from models.location import Floorplan, Location, LocationKind
from schemas.location import FloorplanRead, LocationCreate, LocationUpdate

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


def get_location_or_404(location_id: int, db: Session) -> Location:
    location = db.get(Location, location_id)
    if location is None:
        raise NotFoundError("Lokasi tidak ditemukan")
    return location


def validate_parent(kind: str, parent_id: int | None, db: Session) -> None:
    expected = PARENT_KIND[kind]
    if expected is None:
        if parent_id is not None:
            raise UnprocessableEntityError("Site tidak boleh memiliki induk")
        return
    if parent_id is None:
        raise UnprocessableEntityError(f"{kind} harus memiliki lokasi induk")
    parent = get_location_or_404(parent_id, db)
    if parent.kind != expected:
        raise UnprocessableEntityError(
            f"Induk {kind} harus berjenis {expected}"
        )


def list_locations(db: Session) -> list[Location]:
    return list(db.scalars(select(Location).order_by(Location.sort_order, Location.name)))


def create_location(payload: LocationCreate, db: Session) -> Location:
    validate_parent(payload.kind.value, payload.parent_id, db)
    location = Location(**payload.model_dump(mode="json"))
    db.add(location)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateDataError(
            "Nama lokasi sudah digunakan pada induk ini"
        ) from exc
    db.refresh(location)
    return location


def update_location(
    location_id: int, payload: LocationUpdate, db: Session
) -> Location:
    location = get_location_or_404(location_id, db)
    values = payload.model_dump(exclude_unset=True)
    parent_id = values.get("parent_id", location.parent_id)
    validate_parent(location.kind, parent_id, db)
    if parent_id == location.id:
        raise UnprocessableEntityError("Lokasi tidak dapat menjadi induknya sendiri")
    for key, value in values.items():
        setattr(location, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateDataError(
            "Nama lokasi sudah digunakan pada induk ini"
        ) from exc
    db.refresh(location)
    return location


def delete_location(location_id: int, db: Session) -> None:
    location = get_location_or_404(location_id, db)
    has_devices = db.scalar(select(Device.id).where(Device.room_id == location.id).limit(1))
    has_children = db.scalar(select(Location.id).where(Location.parent_id == location.id).limit(1))
    if has_devices or has_children:
        raise ConflictError(
            "Pindahkan perangkat dan hapus lokasi turunannya terlebih dahulu"
        )
    db.delete(location)
    db.commit()


def floorplan_read(floorplan: Floorplan) -> FloorplanRead:
    return FloorplanRead(
        id=floorplan.id,
        location_id=floorplan.location_id,
        filename=floorplan.filename,
        content_type=floorplan.content_type,
        image_url=f"/api/v1/locations/floorplans/{floorplan.id}/image",
        updated_at=floorplan.updated_at,
    )


def list_floorplans(db: Session) -> list[FloorplanRead]:
    return [floorplan_read(item) for item in db.scalars(select(Floorplan))]


def upload_floorplan(
    location_id: int,
    filename: str | None,
    content_type: str | None,
    content: bytes,
    db: Session,
) -> FloorplanRead:
    location = get_location_or_404(location_id, db)
    if location.kind not in {LocationKind.FLOOR.value, LocationKind.ROOM.value}:
        raise UnprocessableEntityError(
            "Denah hanya dapat dipasang pada lantai atau ruang"
        )
    if not content_type or content_type not in ALLOWED_IMAGE_TYPES:
        raise UnsupportedMediaTypeError("Gunakan gambar PNG, JPG, atau WebP")
    if len(content) > MAX_FLOORPLAN_BYTES:
        raise PayloadTooLargeError("Ukuran denah maksimal 10 MB")
    if not content:
        raise UnprocessableEntityError("Berkas denah kosong")
    if not valid_image_signature(content_type, content):
        raise UnprocessableEntityError("Isi berkas tidak cocok dengan format gambar")
    floorplan = db.scalar(select(Floorplan).where(Floorplan.location_id == location_id))
    if floorplan is None:
        floorplan = Floorplan(location_id=location_id, filename="", content_type="", image_data=b"")
        db.add(floorplan)
    floorplan.filename = (filename or "denah")[:255]
    floorplan.content_type = content_type
    floorplan.image_data = content
    db.commit()
    db.refresh(floorplan)
    return floorplan_read(floorplan)


def get_floorplan_or_404(floorplan_id: int, db: Session) -> Floorplan:
    floorplan = db.get(Floorplan, floorplan_id)
    if floorplan is None:
        raise NotFoundError("Denah tidak ditemukan")
    return floorplan


def get_location_devices(location_id: int, db: Session) -> list[dict]:
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
