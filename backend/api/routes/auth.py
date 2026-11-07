from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db, require_admin
from core.config import settings
from core.security import create_access_token
from models.user import User
from schemas.auth import ApiMessage, LoginRequest, UserRead
from services.auth import authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])
internal_router = APIRouter(prefix="/internal/auth", tags=["internal"], include_in_schema=False)


@router.post("/login", response_model=UserRead)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> User:
    client_ip = request.client.host if request.client else "unknown"
    user = authenticate_user(
        payload.username, payload.password, db, client_identifier=client_ip
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
def me(user: User = Depends(get_current_user)) -> User:
    return user


@internal_router.get("/admin")
def authorize_admin(_: User = Depends(require_admin)) -> Response:
    """Authorize an internal reverse-proxy subrequest for admin-only services."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@internal_router.get("/session")
def authorize_session(_: User = Depends(get_current_user)) -> Response:
    """Authorize an internal reverse-proxy subrequest for any signed-in user."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)
