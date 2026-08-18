from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.dependencies import AdminUser, CurrentUser, DbSession
from app.models import CredentialProfile, Device, Location, LocationKind
from app.schemas import (
    CredentialProfileRead,
    CredentialSecret,
    DeviceCreate,
    DeviceRead,
    DeviceUpdate,
)
from app.security import encrypt_credentials

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceRead])
def list_devices(db: DbSession, _: CurrentUser) -> list[Device]:
    return list(
        db.scalars(select(Device).where(Device.archived_at.is_(None)).order_by(Device.name))
    )


def save_credential_profile(
    payload: CredentialSecret,
    db: DbSession,
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


def validate_references(values: dict, db: DbSession) -> None:
    room_id = values.get("room_id")
    if room_id is not None:
        room = db.get(Location, room_id)
        if room is None or room.kind != LocationKind.ROOM.value:
            raise HTTPException(status_code=422, detail="Lokasi perangkat harus berupa ruang")
    profile_id = values.get("credential_profile_id")
    if profile_id is not None and db.get(CredentialProfile, profile_id) is None:
        raise HTTPException(status_code=422, detail="Profil kredensial tidak ditemukan")


def validate_device_semantics(values: dict, current: Device | None = None) -> None:
    kind = values.get("kind", current.kind if current else None)
    stream_url = values.get("stream_url", current.stream_url if current else "")
    if kind == "cctv" and not stream_url:
        raise HTTPException(status_code=422, detail="CCTV memerlukan URL stream RTSP")


@router.post("", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
def create_device(payload: DeviceCreate, db: DbSession, _: AdminUser) -> Device:
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
        raise HTTPException(status_code=409, detail="Nama perangkat sudah digunakan") from exc
    db.refresh(device)
    return device


def get_device_or_404(device_id: int, db: DbSession) -> Device:
    device = db.get(Device, device_id)
    if device is None or device.archived_at is not None:
        raise HTTPException(status_code=404, detail="Perangkat tidak ditemukan")
    return device


@router.get("/{device_id}", response_model=DeviceRead)
def get_device(device_id: int, db: DbSession, _: CurrentUser) -> Device:
    return get_device_or_404(device_id, db)


@router.patch("/{device_id}", response_model=DeviceRead)
def update_device(device_id: int, payload: DeviceUpdate, db: DbSession, _: AdminUser) -> Device:
    device = get_device_or_404(device_id, db)
    values = payload.model_dump(exclude_unset=True, mode="json", exclude={"credential"})
    if payload.credential is not None:
        values["credential_profile_id"] = save_credential_profile(
            payload.credential, db, device.credential_profile_id
        ).id
    validate_references(values, db)
    validate_device_semantics(values, device)
    for key, value in values.items():
        setattr(device, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Nama perangkat sudah digunakan") from exc
    db.refresh(device)
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: int, db: DbSession, _: AdminUser) -> Response:
    device = get_device_or_404(device_id, db)
    device.archived_at = datetime.now(UTC)
    device.is_active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/credentials/profiles", response_model=list[CredentialProfileRead])
def list_credential_profiles(db: DbSession, _: AdminUser) -> list[CredentialProfile]:
    return list(db.scalars(select(CredentialProfile).order_by(CredentialProfile.name)))
