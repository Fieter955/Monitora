import base64
import hashlib
import json
import os
from datetime import UTC, datetime, timedelta

import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pwdlib import PasswordHash

from app.config import settings

ALGORITHM = "HS256"
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_access_token(user_id: int) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": str(user_id), "exp": expires, "iat": datetime.now(UTC)},
        settings.app_secret_key,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.app_secret_key, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None


def _credential_key() -> bytes:
    source = settings.credential_encryption_key or settings.app_secret_key
    return hashlib.sha256(source.encode("utf-8")).digest()


def encrypt_credentials(payload: dict[str, str]) -> str:
    """Encrypt device credentials with an authenticated AES-256-GCM envelope."""
    nonce = os.urandom(12)
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    encrypted = AESGCM(_credential_key()).encrypt(nonce, raw, b"pantau-credentials-v1")
    return base64.urlsafe_b64encode(nonce + encrypted).decode("ascii")


def decrypt_credentials(value: str) -> dict[str, str]:
    decoded = base64.urlsafe_b64decode(value.encode("ascii"))
    raw = AESGCM(_credential_key()).decrypt(decoded[:12], decoded[12:], b"pantau-credentials-v1")
    payload = json.loads(raw.decode("utf-8"))
    return {str(key): str(item) for key, item in payload.items()}
