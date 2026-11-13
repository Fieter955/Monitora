import re
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from api.routes import auth, devices, locations, monitoring, network, operations, reports, system
from core.config import settings
from core.exceptions import (
    ConflictError,
    DomainException,
    DuplicateDataError,
    ForbiddenError,
    InvalidArgumentError,
    InvalidCredentialsError,
    NotFoundError,
    PayloadTooLargeError,
    ServiceUnavailableError,
    TooManyRequestsError,
    UnAuthorizedError,
    UnprocessableEntityError,
    UnsupportedMediaTypeError,
)

REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/api/docs" if settings.app_env != "production" else None,
    redoc_url=None,
)

if settings.allowed_host_list and settings.allowed_host_list != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_host_list)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    incoming_id = request.headers.get("X-Request-ID", "")
    request_id = incoming_id if REQUEST_ID_RE.match(incoming_id) else uuid.uuid4().hex
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.exception_handler(DomainException)
@app.exception_handler(DuplicateDataError)
@app.exception_handler(ConflictError)
@app.exception_handler(InvalidArgumentError)
@app.exception_handler(NotFoundError)
@app.exception_handler(InvalidCredentialsError)
@app.exception_handler(UnAuthorizedError)
@app.exception_handler(ForbiddenError)
@app.exception_handler(UnprocessableEntityError)
@app.exception_handler(UnsupportedMediaTypeError)
@app.exception_handler(PayloadTooLargeError)
@app.exception_handler(TooManyRequestsError)
@app.exception_handler(ServiceUnavailableError)
def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(
        status_code=exc.status_code,
        headers=headers,
        content={
            "code": exc.code,
            "detail": exc.detail,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


api_prefix = "/api/v1"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(devices.router, prefix=api_prefix)
app.include_router(locations.router, prefix=api_prefix)
app.include_router(network.router, prefix=api_prefix)
app.include_router(operations.router, prefix=api_prefix)
app.include_router(monitoring.router, prefix=api_prefix)
app.include_router(reports.router, prefix=api_prefix)
app.include_router(system.router, prefix=api_prefix)

# Internal reverse-proxy subrequest / discovery endpoints
app.include_router(auth.internal_router)
app.include_router(monitoring.internal_router)
app.include_router(network.internal_router)
app.include_router(system.internal_router)
