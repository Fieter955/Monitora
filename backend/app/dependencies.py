from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.security import decode_access_token

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    user_id = decode_access_token(access_token) if access_token else None
    user = db.get(User, user_id) if user_id else None
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesi tidak valid")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses administrator diperlukan",
        )
    return user


AdminUser = Annotated[User, Depends(require_admin)]
