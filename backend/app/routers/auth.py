from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.config import settings
from app.dependencies import AdminUser, CurrentUser, DbSession
from app.models import User
from app.schemas import ApiMessage, LoginRequest, UserRead
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserRead)
def login(payload: LoginRequest, response: Response, db: DbSession) -> User:
    user = db.scalar(select(User).where(User.username == payload.username.strip()))
    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nama pengguna atau kata sandi salah",
        )
    response.set_cookie(
        key="access_token",
        value=create_access_token(user.id),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    return user


@router.post("/logout", response_model=ApiMessage)
def logout(response: Response) -> ApiMessage:
    response.delete_cookie("access_token", path="/")
    return ApiMessage(message="Sesi telah diakhiri")


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser) -> User:
    return user


def authorize_admin(_: AdminUser) -> Response:
    """Authorize an internal reverse-proxy subrequest for admin-only services."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def authorize_session(_: CurrentUser) -> Response:
    """Authorize an internal reverse-proxy subrequest for any signed-in user."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)
