from collections import defaultdict
from threading import Lock
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.exceptions import InvalidCredentialsError, TooManyRequestsError
from core.security import verify_password
from models.user import User

_login_failures: dict[str, list[float]] = defaultdict(list)
_lock = Lock()

MAX_FAILED_ATTEMPTS = 5
FAILURE_WINDOW_SECONDS = 60.0


def check_rate_limit(key: str) -> None:
    now = time.monotonic()
    with _lock:
        timestamps = [t for t in _login_failures[key] if now - t < FAILURE_WINDOW_SECONDS]
        _login_failures[key] = timestamps
        if len(timestamps) >= MAX_FAILED_ATTEMPTS:
            raise TooManyRequestsError(
                "Terlalu banyak percobaan masuk yang gagal. Silakan coba lagi nanti."
            )


def record_login_failure(key: str) -> None:
    now = time.monotonic()
    with _lock:
        _login_failures[key].append(now)


def record_login_success(key: str) -> None:
    with _lock:
        _login_failures.pop(key, None)


def reset_login_limits() -> None:
    """Mengosongkan catatan laju percobaan login (untuk testing atau pembersihan)."""
    with _lock:
        _login_failures.clear()


def authenticate_user(
    username: str,
    password: str,
    db: Session,
    client_identifier: str = "",
) -> User:
    rate_limit_key = (
        f"{client_identifier}:{username.strip().lower()}"
        if client_identifier
        else username.strip().lower()
    )
    check_rate_limit(rate_limit_key)

    user = db.scalar(select(User).where(User.username == username.strip()))
    if (
        user is None
        or not user.is_active
        or not verify_password(password, user.password_hash)
    ):
        record_login_failure(rate_limit_key)
        raise InvalidCredentialsError("Nama pengguna atau kata sandi salah")

    record_login_success(rate_limit_key)
    return user
