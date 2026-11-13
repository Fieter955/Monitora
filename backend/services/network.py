# quality: ignore[Q303] modul orkestrasi visibilitas jaringan, discovery, dan topologi
import re
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import settings
from core.exceptions import (
    NotFoundError,
    ServiceUnavailableError,
    UnprocessableEntityError,
)
from core.security import decrypt_credentials
from models.credential import CredentialProfile
from models.device import Device, DeviceKind
from models.network import NetworkLink, NetworkPort, PortExpectation
from schemas.monitoring import SnmpInterfaceRead
from schemas.network import (
    ConnectionTestRequest,
    ConnectionTestResult,
    DeviceHealthRead,
    DeviceIssue,
    DiscoveryResult,
    ManualLinkCreate,
    PortExpectationsUpdate,
    TopologyEdge,
    TopologyNode,
    TopologyRead,
)
from services.device import get_device_or_404
from services.librenms import LibreNMSUnavailable, librenms_client
from services.network_sync import (
    NETWORK_KINDS,
    clear_legacy_observation,
    device_health,
    port_to_read,
    sync_cctv_device,
    sync_links,
    sync_network_device,
)
from services.probes import icmp_probe, rtsp_probe, tcp_probe
from services.prometheus import prometheus_client


def librenms_enabled() -> bool:
    return settings.enable_librenms and not settings.native_windows


def sync_prometheus_interfaces(device: Device, db: Session) -> list[NetworkPort]:
    interfaces = prometheus_client.snmp_interfaces(device.prometheus_target)
    existing = {
        item.source_port_id: item
        for item in db.scalars(select(NetworkPort).where(NetworkPort.device_id == device.id))
    }
    ports: list[NetworkPort] = []
    now = datetime.now(UTC)
    for interface in interfaces:
        port = existing.get(interface.if_index)
        if port is None:
            port = NetworkPort(device_id=device.id, source_port_id=interface.if_index)
            db.add(port)
        port.if_index = interface.if_index
        port.name = interface.if_name
        port.description = interface.if_description
        port.alias = interface.if_alias
        port.oper_status = (
            "up" if interface.oper_up else "down" if interface.oper_up is False else "unknown"
        )
        port.last_seen_at = now
        ports.append(port)
    if ports:
        device.capabilities = {**(device.capabilities or {}), "snmp": True, "if_mib": True}
        device.monitoring_level = "basic"
        db.flush()
    return ports


def combine_reachability(health: DeviceHealthRead, status: str | None) -> DeviceHealthRead:
    if health.status != "unknown" or status not in {"online", "offline"}:
        return health
    if status == "online":
        return health.model_copy(
            update={"status": "healthy", "reason": "Target monitoring dapat dijangkau"}
        )
    issues = [
        *health.issues,
        DeviceIssue(
            code="target_unreachable",
            severity="critical",
            title="Target tidak terjangkau",
            detail="Prometheus gagal mengambil data dari target perangkat.",
        ),
    ]
    return health.model_copy(
        update={"status": "critical", "reason": "Target monitoring offline", "issues": issues}
    )


def resolve_test_credentials(
    payload: ConnectionTestRequest, db: Session
) -> dict[str, str] | None:
    if payload.credential:
        return payload.credential.model_dump(exclude_none=True)
    if payload.credential_profile_id:
        stored = db.get(CredentialProfile, payload.credential_profile_id)
        if stored:
            return decrypt_credentials(stored.encrypted_payload)
    return None


def test_icmp_target(address: str) -> ConnectionTestResult:
    result = icmp_probe(address)
    return ConnectionTestResult(
        reachable=result.reachable,
        provider_available=result.status != "unavailable",
        capabilities=["icmp"] if result.reachable else [],
        message=result.reason,
        latency_ms=result.latency_ms,
    )


def test_cctv_target(
    payload: ConnectionTestRequest, credentials: dict[str, str] | None
) -> ConnectionTestResult:
    if payload.stream_url:
        result = rtsp_probe(payload.stream_url, credentials)
    else:
        result = tcp_probe(payload.address, 554)
    return ConnectionTestResult(
        reachable=result.reachable,
        provider_available=librenms_client.configured,
        capabilities=["rtsp"] if result.reachable and payload.stream_url else [],
        message=result.reason,
        latency_ms=result.latency_ms,
    )


def test_network_target() -> ConnectionTestResult:
    if not librenms_enabled():
        return ConnectionTestResult(
            reachable=True,
            provider_available=True,
            capabilities=["snmp", "if_mib"],
            message=(
                "Target akan diuji oleh SNMP Exporter. Setelah disimpan, tunggu satu siklus "
                "Prometheus sebelum memilih interface WAN."
            ),
        )
    if not librenms_client.configured:
        return ConnectionTestResult(
            reachable=False,
            provider_available=False,
            capabilities=[],
            message="Token API LibreNMS belum dikonfigurasi; alamat belum diuji melalui SNMP.",
        )
    try:
        librenms_client.health()
    except LibreNMSUnavailable as exc:
        return ConnectionTestResult(
            reachable=False,
            provider_available=False,
            capabilities=[],
            message=str(exc),
        )
    return ConnectionTestResult(
        reachable=True,
        provider_available=True,
        capabilities=["librenms", "snmp"],
        message="LibreNMS siap. Discovery penuh dijalankan setelah perangkat disimpan.",
    )


def test_tcp_target(address: str, port: int = 80) -> ConnectionTestResult:
    result = tcp_probe(address, port)
    return ConnectionTestResult(
        reachable=result.reachable,
        provider_available=True,
        capabilities=["tcp"] if result.reachable else [],
        message=result.reason,
        latency_ms=result.latency_ms,
    )


def test_connection(
    payload: ConnectionTestRequest,
    db: Session,
) -> ConnectionTestResult:
    credentials = resolve_test_credentials(payload, db)
    if payload.prometheus_job == "icmp":
        return test_icmp_target(payload.address)
    if payload.kind == DeviceKind.CCTV:
        return test_cctv_target(payload, credentials)
    if payload.kind.value in NETWORK_KINDS:
        return test_network_target()
    return test_tcp_target(payload.address, 80)


def discover_icmp_network(device: Device, db: Session) -> DiscoveryResult:
    device.monitoring_level = "basic"
    device.capabilities = {"icmp": True}
    clear_legacy_observation(db, device.id, source="librenms")
    db.commit()
    return DiscoveryResult(
        device_id=device.id,
        state="ready",
        message="Monitoring ICMP aktif. Perangkat ini tidak menjalankan discovery SNMP atau port.",
        capabilities=["icmp"],
        ports=[],
    )


def discover_snmp_network(device: Device, db: Session) -> DiscoveryResult:
    if not librenms_enabled():
        ports = sync_prometheus_interfaces(device, db)
        db.commit()
        return DiscoveryResult(
            device_id=device.id,
            state="ready" if ports else "partial",
            message=(
                f"{len(ports)} interface SNMP ditemukan."
                if ports
                else "Target tersimpan. Tunggu 30-60 detik lalu jalankan discovery kembali."
            ),
            capabilities=list((device.capabilities or {}).keys()),
            ports=[port_to_read(port, None) for port in ports],
        )
    librenms_id = device.librenms_device_id
    if librenms_id is None:
        ports = sync_network_device(device, db)
        librenms_id = device.librenms_device_id
    else:
        ports = sync_network_device(device, db)
    if librenms_id:
        librenms_client.discover_device(librenms_id)
    db.commit()
    return DiscoveryResult(
        device_id=device.id,
        state="ready" if ports else "partial",
        message=(
            f"{len(ports)} port ditemukan. Konfirmasikan fungsi setiap port."
            if ports
            else "Discovery dijadwalkan di LibreNMS; port belum tersedia pada siklus ini."
        ),
        capabilities=list(device.capabilities.keys()),
        ports=[port_to_read(port, None) for port in ports],
    )


def discover_cctv(device: Device, db: Session) -> DiscoveryResult:
    sync_cctv_device(device, db)
    db.commit()
    health = device_health(device, db)
    return DiscoveryResult(
        device_id=device.id,
        state="ready" if health.status == "healthy" else "partial",
        message=health.reason or "Pemeriksaan CCTV selesai.",
        capabilities=list(device.capabilities.keys()),
        ports=[],
    )


def discover_basic(device: Device, db: Session) -> DiscoveryResult:
    device.monitoring_level = "limited" if device.kind == DeviceKind.HUB.value else "basic"
    db.commit()
    return DiscoveryResult(
        device_id=device.id,
        state="partial",
        message="Perangkat ini hanya dapat dipantau dari probe dasar atau perangkat upstream.",
        capabilities=[],
        ports=[],
    )


def discover_device(device_id: int, db: Session) -> DiscoveryResult:
    device = get_device_or_404(device_id, db)
    try:
        if device.kind in NETWORK_KINDS and device.prometheus_job == "icmp":
            return discover_icmp_network(device, db)
        if device.kind in NETWORK_KINDS:
            return discover_snmp_network(device, db)
        if device.kind == DeviceKind.CCTV.value:
            return discover_cctv(device, db)
        return discover_basic(device, db)
    except LibreNMSUnavailable as exc:
        db.rollback()
        return DiscoveryResult(
            device_id=device.id,
            state="unavailable",
            message=str(exc),
            capabilities=[],
            ports=[],
        )
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        db.rollback()
        return DiscoveryResult(
            device_id=device.id,
            state="unavailable",
            message=f"Prometheus/SNMP Exporter belum siap: {exc}",
            capabilities=[],
            ports=[],
        )


def get_snmp_interfaces(device_id: int, db: Session) -> list[SnmpInterfaceRead]:
    device = get_device_or_404(device_id, db)
    if device.prometheus_job != "snmp":
        raise UnprocessableEntityError("Perangkat tidak menggunakan monitoring SNMP")
    try:
        return prometheus_client.snmp_interfaces(device.prometheus_target)
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        raise ServiceUnavailableError(f"Data interface SNMP belum tersedia: {exc}") from exc


def get_discovery_state(device_id: int, db: Session) -> DiscoveryResult:
    device = get_device_or_404(device_id, db)
    health = device_health(device, db)
    icmp_only = device.kind in NETWORK_KINDS and device.prometheus_job == "icmp"
    return DiscoveryResult(
        device_id=device.id,
        state=(
            "ready"
            if health.ports or device.kind == DeviceKind.CCTV.value or icmp_only
            else "partial"
        ),
        message=(
            "Monitoring ICMP aktif; discovery port tidak digunakan."
            if icmp_only
            else f"{len(health.ports)} port tersedia."
        ),
        capabilities=list((device.capabilities or {}).keys()),
        ports=health.ports,
    )


def update_port_expectations(
    device_id: int,
    payload: PortExpectationsUpdate,
    db: Session,
) -> DeviceHealthRead:
    device = get_device_or_404(device_id, db)
    ports = {
        port.id: port
        for port in db.scalars(select(NetworkPort).where(NetworkPort.device_id == device.id))
    }
    requested = {item.port_id for item in payload.ports}
    if not requested.issubset(ports):
        raise UnprocessableEntityError("Ada port yang bukan milik perangkat ini")
    for item in payload.ports:
        expectation = db.scalar(
            select(PortExpectation).where(PortExpectation.port_id == item.port_id)
        )
        if expectation is None:
            expectation = PortExpectation(port_id=item.port_id)
            db.add(expectation)
        expectation.mode = item.mode.value
        expectation.expected_device_id = item.expected_device_id
        expectation.label = item.label
        expectation.consecutive_mismatches = 0
    db.commit()
    return device_health(device, db)


def get_device_health(device_id: int, db: Session) -> DeviceHealthRead:
    device = get_device_or_404(device_id, db)
    health = device_health(device, db)
    if health.status == "unknown":
        summary = prometheus_client.summary([device])
        metric_status = summary.devices[0].status if summary.devices else None
        health = combine_reachability(health, metric_status)
    return health


def create_manual_link(payload: ManualLinkCreate, db: Session) -> None:
    local = get_device_or_404(payload.local_device_id, db)
    get_device_or_404(payload.remote_device_id, db)
    if payload.local_device_id == payload.remote_device_id:
        raise UnprocessableEntityError("Koneksi harus menghubungkan dua perangkat")
    for port_id, owner in (
        (payload.local_port_id, payload.local_device_id),
        (payload.remote_port_id, payload.remote_device_id),
    ):
        if (
            port_id
            and db.scalar(
                select(NetworkPort.id).where(
                    NetworkPort.id == port_id, NetworkPort.device_id == owner
                )
            )
            is None
        ):
            raise UnprocessableEntityError("Port tidak sesuai dengan perangkat")
    db.add(
        NetworkLink(
            source_key=f"manual:{uuid4()}",
            origin="manual",
            local_device_id=local.id,
            local_port_id=payload.local_port_id,
            remote_device_id=payload.remote_device_id,
            remote_port_id=payload.remote_port_id,
            active=True,
        )
    )
    db.commit()


def find_gateway_path_ids(
    focus_device_id: int,
    gateway_ids: set[int],
    adjacency: dict[int, set[int]],
) -> tuple[set[int], bool]:
    parents: dict[int, int | None] = {gateway: None for gateway in gateway_ids}
    queue = list(gateway_ids)
    while queue and focus_device_id not in parents:
        current = queue.pop(0)
        for neighbor in adjacency.get(current, set()):
            if neighbor not in parents:
                parents[neighbor] = current
                queue.append(neighbor)
    path_complete = focus_device_id in parents
    if not path_complete:
        return adjacency.get(focus_device_id, set()), False
    path_ids: set[int] = set()
    node: int | None = focus_device_id
    while node is not None:
        path_ids.add(node)
        node = parents[node]
    return path_ids, True


def _build_topology_nodes(devices: list[Device], db: Session) -> list[TopologyNode]:
    prometheus_summary = prometheus_client.summary(devices)
    prometheus_status = {item.device_id: item.status for item in prometheus_summary.devices}
    nodes: list[TopologyNode] = []
    for device in devices:
        health = combine_reachability(device_health(device, db), prometheus_status.get(device.id))
        nodes.append(
            TopologyNode(
                id=device.id,
                name=device.name,
                kind=DeviceKind(device.kind),
                address=device.address,
                room_id=device.room_id,
                location=device.location,
                status=health.status,
                monitoring_level=device.monitoring_level,
                network_role=device.network_role,
            )
        )
    return nodes


def _build_topology_edges(device_ids: set[int], db: Session) -> list[TopologyEdge]:
    ports = {port.id: port for port in db.scalars(select(NetworkPort))}
    edges: list[TopologyEdge] = []
    for link in db.scalars(select(NetworkLink).where(NetworkLink.active.is_(True))):
        if link.local_device_id not in device_ids:
            continue
        local_port = ports.get(link.local_port_id)
        remote_port = ports.get(link.remote_port_id)
        utilization = None
        if local_port and local_port.speed_bps:
            utilization = round(
                max(local_port.rx_bps or 0, local_port.tx_bps or 0) / local_port.speed_bps * 100,
                2,
            )
        edges.append(
            TopologyEdge(
                id=link.source_key,
                origin=link.origin,
                source_device_id=link.local_device_id,
                target_device_id=link.remote_device_id,
                source_port=local_port.name if local_port else "",
                target_port=remote_port.name if remote_port else link.remote_port_name,
                target_name=link.remote_name,
                active=link.active,
                utilization_percent=utilization,
            )
        )
    return edges


def get_topology(
    db: Session,
    room_id: int | None = None,
    focus_device_id: int | None = None,
    scope: Literal["all", "neighbors", "path"] = "all",
) -> TopologyRead:
    query = select(Device).where(Device.archived_at.is_(None), Device.is_active.is_(True))
    if room_id is not None:
        query = query.where(Device.room_id == room_id)
    devices = list(db.scalars(query.order_by(Device.name)))
    device_ids = {device.id for device in devices}
    nodes = _build_topology_nodes(devices, db)
    edges = _build_topology_edges(device_ids, db)
    path_complete: bool | None = None
    if focus_device_id is not None:
        if focus_device_id not in device_ids:
            raise NotFoundError("Perangkat fokus tidak ditemukan")
        adjacency: dict[int, set[int]] = {device_id: set() for device_id in device_ids}
        for edge in edges:
            if edge.target_device_id in device_ids:
                adjacency[edge.source_device_id].add(edge.target_device_id)
                adjacency[edge.target_device_id].add(edge.source_device_id)

        selected_ids = {focus_device_id}
        if scope == "neighbors":
            selected_ids |= adjacency[focus_device_id]
        elif scope == "path":
            gateway_ids = {node.id for node in nodes if node.network_role.value == "gateway"}
            path_ids, path_complete = find_gateway_path_ids(
                focus_device_id, gateway_ids, adjacency
            )
            selected_ids |= path_ids

        if scope != "all":
            nodes = [node for node in nodes if node.id in selected_ids]
            edges = [
                edge
                for edge in edges
                if edge.source_device_id in selected_ids
                and edge.target_device_id in selected_ids
            ]

    return TopologyRead(
        generated_at=datetime.now(UTC),
        nodes=nodes,
        edges=edges,
        focus_device_id=focus_device_id,
        path_complete=path_complete,
    )


def sync_network(db: Session) -> TopologyRead:
    try:
        for device in db.scalars(
            select(Device).where(
                Device.kind.in_(NETWORK_KINDS),
                Device.is_active.is_(True),
                Device.archived_at.is_(None),
            )
        ):
            sync_network_device(device, db)
        sync_links(db)
        db.commit()
    except LibreNMSUnavailable as exc:
        db.rollback()
        raise ServiceUnavailableError(str(exc)) from exc
    return get_topology(db)


def get_internal_metrics(db: Session) -> str:
    lines = [
        "# HELP pantau_device_issue Device issue state (1 means active)",
        "# TYPE pantau_device_issue gauge",
    ]
    for device in db.scalars(
        select(Device).where(Device.is_active.is_(True), Device.archived_at.is_(None))
    ):
        health = device_health(device, db)
        active_codes = {issue.code for issue in health.issues}
        for code in (
            "required_port_down",
            "unexpected_port_active",
            "cctv_stream_down",
            "monitoring_data_stale",
            "network_device_down",
            "monitoring_unavailable",
        ):
            safe_name = re.sub(r"[\r\n]+", " ", device.name).replace('"', "'").replace("\\", "")
            labels = f'device_id="{device.id}",device_name="{safe_name}",issue="{code}"'
            lines.append(f"pantau_device_issue{{{labels}}} {1 if code in active_codes else 0}")
    return "\n".join(lines) + "\n"
