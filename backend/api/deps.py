from collections.abc import Generator

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from core.exceptions import ForbiddenError, UnAuthorizedError
from core.security import decode_access_token
from db.session import SessionLocal
from models.user import User, UserRole


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    access_token: str | None = Cookie(default=None),
) -> User:
    user_id = decode_access_token(access_token) if access_token else None
    user = db.get(User, user_id) if user_id else None
    if user is None or not user.is_active:
        raise UnAuthorizedError("Sesi tidak valid")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN.value:
        raise ForbiddenError("Akses administrator diperlukan")
    return user
