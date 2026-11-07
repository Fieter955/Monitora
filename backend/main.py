from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from api.routes import auth, devices, locations, monitoring, network, operations, reports, system
from core.config import settings
from core.exceptions import (
    ConflictError,
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

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/api/docs" if settings.app_env != "production" else None,
    redoc_url=None,
)

if settings.allowed_host_list and settings.allowed_host_list != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_host_list)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.exception_handler(DuplicateDataError)
def duplicate_data_error_handler(request: Request, exc: DuplicateDataError):
    return JSONResponse(status_code=409, content={"detail": exc.detail})


@app.exception_handler(ConflictError)
def conflict_error_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": exc.detail})


@app.exception_handler(InvalidArgumentError)
def invalid_argument_error_handler(request: Request, exc: InvalidArgumentError):
    return JSONResponse(status_code=400, content={"detail": exc.detail})


@app.exception_handler(NotFoundError)
def not_found_error_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": exc.detail})


@app.exception_handler(InvalidCredentialsError)
def invalid_credentials_error_handler(request: Request, exc: InvalidCredentialsError):
    return JSONResponse(
        status_code=401,
        headers={"WWW-Authenticate": "Bearer"},
        content={"detail": exc.detail},
    )


@app.exception_handler(UnAuthorizedError)
def un_authorized_error_handler(request: Request, exc: UnAuthorizedError):
    return JSONResponse(
        status_code=401,
        headers={"WWW-Authenticate": "Bearer"},
        content={"detail": exc.detail},
    )


@app.exception_handler(ForbiddenError)
def forbidden_error_handler(request: Request, exc: ForbiddenError):
    return JSONResponse(status_code=403, content={"detail": exc.detail})


@app.exception_handler(UnprocessableEntityError)
def unprocessable_entity_error_handler(request: Request, exc: UnprocessableEntityError):
    return JSONResponse(status_code=422, content={"detail": exc.detail})


@app.exception_handler(UnsupportedMediaTypeError)
def unsupported_media_type_error_handler(request: Request, exc: UnsupportedMediaTypeError):
    return JSONResponse(status_code=415, content={"detail": exc.detail})


@app.exception_handler(PayloadTooLargeError)
def payload_too_large_error_handler(request: Request, exc: PayloadTooLargeError):
    return JSONResponse(status_code=413, content={"detail": exc.detail})


@app.exception_handler(TooManyRequestsError)
def too_many_requests_error_handler(request: Request, exc: TooManyRequestsError):
    return JSONResponse(status_code=429, content={"detail": exc.detail})


@app.exception_handler(ServiceUnavailableError)
def service_unavailable_error_handler(request: Request, exc: ServiceUnavailableError):
    return JSONResponse(status_code=503, content={"detail": exc.detail})


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
