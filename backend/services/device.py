from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.exceptions import DuplicateDataError, NotFoundError, UnprocessableEntityError
from core.security import encrypt_credentials
from models.credential import CredentialProfile
from models.device import Device
from models.location import Location, LocationKind
from schemas.credential import CredentialSecret
from schemas.device import BulkPlacementUpdate, DeviceCreate, DeviceUpdate
from services.network_sync import clear_legacy_observation


def list_devices(db: Session) -> list[Device]:
    return list(
        db.scalars(select(Device).where(Device.archived_at.is_(None)).order_by(Device.name))
    )


def bulk_place_devices(payload: BulkPlacementUpdate, db: Session) -> list[Device]:
    room = db.get(Location, payload.room_id)
    if room is None or room.kind != LocationKind.ROOM.value:
        raise UnprocessableEntityError("Lokasi penempatan harus berupa ruang")
    if len(set(payload.device_ids)) != len(payload.device_ids):
        raise UnprocessableEntityError("Daftar perangkat memuat ID duplikat")
    devices = list(
        db.scalars(
            select(Device).where(
                Device.id.in_(payload.device_ids), Device.archived_at.is_(None)
            )
        )
    )
    if len(devices) != len(payload.device_ids):
        raise NotFoundError("Satu atau lebih perangkat tidak ditemukan")
    existing_rooms = {device.room_id for device in devices if device.room_id is not None}
    if existing_rooms and existing_rooms != {payload.room_id}:
        raise UnprocessableEntityError(
            "Penempatan massal hanya boleh untuk perangkat dalam ruang yang sama"
        )
    for device in devices:
        device.room_id = payload.room_id
        device.floorplan_x = payload.floorplan_x
        device.floorplan_y = payload.floorplan_y
        device.physical_group = payload.physical_group.strip()
    db.commit()
    for device in devices:
        db.refresh(device)
    return sorted(devices, key=lambda item: item.name.casefold())


def list_credential_profiles(db: Session) -> list[CredentialProfile]:
    return list(db.scalars(select(CredentialProfile).order_by(CredentialProfile.name)))


def save_credential_profile(
    payload: CredentialSecret,
    db: Session,
    profile_id: int | None = None,
) -> CredentialProfile:
    secret = payload.model_dump(exclude={"name", "kind"}, exclude_none=True)
    profile = db.get(CredentialProfile, profile_id) if profile_id else None
    if profile is None:
        profile = CredentialProfile(name="", kind="", encrypted_payload="")
        db.add(profile)
    profile.name = payload.name.strip()
    profile.kind = payload.kind.value
    profile.encrypted_payload = encrypt_credentials(secret)
    db.flush()
    return profile


def validate_references(values: dict, db: Session) -> None:
    room_id = values.get("room_id")
    if room_id is not None:
        room = db.get(Location, room_id)
        if room is None or room.kind != LocationKind.ROOM.value:
            raise UnprocessableEntityError("Lokasi perangkat harus berupa ruang")
    profile_id = values.get("credential_profile_id")
    if profile_id is not None and db.get(CredentialProfile, profile_id) is None:
        raise UnprocessableEntityError("Profil kredensial tidak ditemukan")


def validate_device_semantics(values: dict, current: Device | None = None) -> None:
    kind = values.get("kind", current.kind if current else None)
    stream_url = values.get("stream_url", current.stream_url if current else "")
    if kind == "cctv" and not stream_url:
        raise UnprocessableEntityError("CCTV memerlukan URL stream RTSP")


def create_device(payload: DeviceCreate, db: Session) -> Device:
    values = payload.model_dump(mode="json", exclude={"credential"})
    if payload.credential is not None:
        values["credential_profile_id"] = save_credential_profile(payload.credential, db).id
    validate_references(values, db)
    validate_device_semantics(values)
    device = Device(**values)
    db.add(device)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateDataError(
            "Nama perangkat atau label aset sudah digunakan"
        ) from exc
    db.refresh(device)
    return device


def get_device_or_404(device_id: int, db: Session) -> Device:
    device = db.get(Device, device_id)
    if device is None or device.archived_at is not None:
        raise NotFoundError("Perangkat tidak ditemukan")
    return device


def update_device(device_id: int, payload: DeviceUpdate, db: Session) -> Device:
    device = get_device_or_404(device_id, db)
    values = payload.model_dump(exclude_unset=True, mode="json", exclude={"credential"})
    if payload.credential is not None:
        values["credential_profile_id"] = save_credential_profile(
            payload.credential, db, device.credential_profile_id
        ).id
    validate_references(values, db)
    validate_device_semantics(values, device)
    if (
        values.get("prometheus_job") == "icmp"
        and device.prometheus_job != "icmp"
    ):
        values["credential_profile_id"] = None
        clear_legacy_observation(db, device.id, source="librenms")
    for key, value in values.items():
        setattr(device, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateDataError(
            "Nama perangkat atau label aset sudah digunakan"
        ) from exc
    db.refresh(device)
    return device


def delete_device(device_id: int, db: Session) -> None:
    device = get_device_or_404(device_id, db)
    device.archived_at = datetime.now(UTC)
    device.is_active = False
    db.commit()
