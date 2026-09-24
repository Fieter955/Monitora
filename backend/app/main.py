from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.routers import auth, devices, locations, monitoring, network, operations, reports, system

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

# These endpoints are reachable only on the internal Docker network. Nginx does
# not proxy /internal, so Prometheus can discover inventory without public access.
app.add_api_route(
    "/internal/auth/admin",
    auth.authorize_admin,
    methods=["GET"],
    include_in_schema=False,
)
app.add_api_route(
    "/internal/auth/session",
    auth.authorize_session,
    methods=["GET"],
    include_in_schema=False,
)
app.add_api_route(
    "/internal/prometheus/discovery/node",
    monitoring.node_discovery,
    methods=["GET"],
    include_in_schema=False,
)
app.add_api_route(
    "/internal/prometheus/discovery/windows",
    monitoring.windows_discovery,
    methods=["GET"],
    include_in_schema=False,
)
app.add_api_route(
    "/internal/prometheus/network-metrics",
    network.internal_metrics,
    methods=["GET"],
    include_in_schema=False,
)
app.add_api_route(
    "/internal/prometheus/discovery/blackbox",
    monitoring.blackbox_discovery,
    methods=["GET"],
    include_in_schema=False,
)
app.add_api_route(
    "/internal/prometheus/discovery/icmp",
    monitoring.icmp_discovery,
    methods=["GET"],
    include_in_schema=False,
)
app.add_api_route(
    "/internal/prometheus/discovery/gateway",
    monitoring.gateway_discovery,
    methods=["GET"],
    include_in_schema=False,
)
app.add_api_route(
    "/internal/prometheus/discovery/snmp",
    monitoring.snmp_discovery,
    methods=["GET"],
    include_in_schema=False,
)
