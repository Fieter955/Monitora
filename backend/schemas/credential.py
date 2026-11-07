from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.credential import CredentialKind


class CredentialSecret(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    kind: CredentialKind
    community: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=512)
    auth_protocol: str | None = Field(default=None, max_length=30)
    privacy_protocol: str | None = Field(default=None, max_length=30)
    privacy_password: str | None = Field(default=None, max_length=512)


class CredentialProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    kind: CredentialKind
    created_at: datetime
