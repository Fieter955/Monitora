from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from models.user import utcnow


class CredentialKind(StrEnum):
    SNMP_V2C = "snmp_v2c"
    SNMP_V3 = "snmp_v3"
    ONVIF_RTSP = "onvif_rtsp"


class CredentialProfile(Base):
    __tablename__ = "credential_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(24))
    encrypted_payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
