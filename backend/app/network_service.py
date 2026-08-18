from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.librenms import LibreNMSClient, LibreNMSUnavailable, librenms_client
from app.models import (
    CredentialProfile,
    Device,
    DeviceKind,
    DeviceObservation,
    NetworkLink,
    NetworkPort,
    PortExpectation,
    PortExpectationMode,
)
from app.probes import rtsp_probe, tcp_probe
from app.schemas import DeviceHealthRead, DeviceIssue, NetworkPortRead
from app.security import decrypt_credentials

NETWORK_KINDS = {
    DeviceKind.ROUTER.value,
    DeviceKind.SWITCH.value,
    DeviceKind.ACCESS_POINT.value,
}


def utcnow() -> datetime:
    return datetime.now(UTC)


def as_int(value: Any) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def as_float(value: Any, multiplier: float = 1.0) -> float | None:
    try:
        return round(float(value) * multiplier, 2) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def credentials_for(device: Device, db: Session) -> dict[str, str] | None:
    if not device.credential_profile_id:
        return None
    profile = db.get(CredentialProfile, device.credential_profile_id)
    if profile is None:
        return None
    payload = decrypt_credentials(profile.encrypted_payload)
    payload["kind"] = profile.kind
    return payload


def add_device_to_librenms(
    device: Device,
    db: Session,
    client: LibreNMSClient = librenms_client,
) -> int:
    if device.librenms_device_id:
        return device.librenms_device_id
    device_id = client.add_device(
        device.address,
        device.name,
        device.location,
        credentials_for(device, db),
    )
    device.librenms_device_id = device_id
    device.monitoring_level = "full"
    db.flush()
    return device_id


def sync_network_device(
    device: Device,
    db: Session,
    client: LibreNMSClient = librenms_client,
) -> list[NetworkPort]:
    librenms_id = add_device_to_librenms(device, db, client)
    remote = client.get_device(librenms_id)
    ports = client.get_ports(librenms_id)
    now = utcnow()
    is_online = str(remote.get("status", "0")) in {"1", "true", "True"}
    device.last_seen_at = now if is_online else device.last_seen_at
    observation = db.scalar(
        select(DeviceObservation).where(DeviceObservation.device_id == device.id)
    )
    if observation is None:
        observation = DeviceObservation(device_id=device.id, source="librenms")
        db.add(observation)
    observation.source = "librenms"
    observation.status = "online" if is_online else "offline"
    observation.reason = (
        "LibreNMS menerima respons perangkat"
        if is_online
        else "LibreNMS menandai perangkat tidak terjangkau"
    )
    observation.checked_at = now
    device.capabilities = {
        "snmp": str(remote.get("snmp_disable", "0")) not in {"1", "true", "True"},
        "os": remote.get("os"),
        "hardware": remote.get("hardware"),
        "serial": remote.get("serial"),
        "ports": len(ports),
    }

    existing = {
        port.source_port_id: port
        for port in db.scalars(select(NetworkPort).where(NetworkPort.device_id == device.id))
    }
    synced: list[NetworkPort] = []
    for item in ports:
        source_port_id = as_int(item.get("port_id"))
        if source_port_id is None:
            continue
        port = existing.get(source_port_id)
        if port is None:
            port = NetworkPort(device_id=device.id, source_port_id=source_port_id, name="unknown")
            db.add(port)
        speed = as_int(item.get("ifSpeed"))
        if not speed and as_int(item.get("ifHighSpeed")):
            speed = as_int(item.get("ifHighSpeed")) * 1_000_000
        port.if_index = as_int(item.get("ifIndex"))
        port.name = str(item.get("ifName") or item.get("ifDescr") or source_port_id)
        port.description = str(item.get("ifDescr") or "")
        port.alias = str(item.get("ifAlias") or "")
        port.admin_status = str(item.get("ifAdminStatus") or "unknown").lower()
        port.oper_status = str(item.get("ifOperStatus") or "unknown").lower()
        port.speed_bps = speed
        port.rx_bps = as_float(item.get("ifInOctets_rate"), 8)
        port.tx_bps = as_float(item.get("ifOutOctets_rate"), 8)
        port.errors_in = as_float(item.get("ifInErrors_delta"))
        port.errors_out = as_float(item.get("ifOutErrors_delta"))
        port.discards_in = as_float(item.get("ifInDiscards_delta"))
        port.discards_out = as_float(item.get("ifOutDiscards_delta"))
        port.mac_address = str(item.get("ifPhysAddress") or "")
        port.last_seen_at = now
        synced.append(port)
    db.flush()
    update_expectation_counters(synced, db)
    return synced


def update_expectation_counters(ports: list[NetworkPort], db: Session) -> None:
    if not ports:
        return
    expectations = {
        item.port_id: item
        for item in db.scalars(
            select(PortExpectation).where(PortExpectation.port_id.in_([port.id for port in ports]))
        )
    }
    for port in ports:
        expectation = expectations.get(port.id)
        if expectation is None:
            continue
        mismatch = (
            expectation.mode == PortExpectationMode.REQUIRED.value and port.oper_status != "up"
        ) or (expectation.mode == PortExpectationMode.SPARE.value and port.oper_status == "up")
        expectation.consecutive_mismatches = (
            expectation.consecutive_mismatches + 1 if mismatch else 0
        )


def sync_links(db: Session, client: LibreNMSClient = librenms_client) -> None:
    links = client.get_links()
    devices_by_remote = {
        device.librenms_device_id: device
        for device in db.scalars(select(Device).where(Device.librenms_device_id.is_not(None)))
    }
    ports_by_remote = {port.source_port_id: port for port in db.scalars(select(NetworkPort))}
    now = utcnow()
    seen: set[str] = set()
    for item in links:
        source_id = as_int(item.get("local_device_id"))
        local_device = devices_by_remote.get(source_id)
        if local_device is None:
            continue
        source_key = f"librenms:{item.get('id')}"
        seen.add(source_key)
        link = db.scalar(select(NetworkLink).where(NetworkLink.source_key == source_key))
        if link is None:
            link = NetworkLink(
                source_key=source_key,
                origin=str(item.get("protocol") or "discovered").lower(),
                local_device_id=local_device.id,
            )
            db.add(link)
        remote_device = devices_by_remote.get(as_int(item.get("remote_device_id")))
        local_port = ports_by_remote.get(as_int(item.get("local_port_id")))
        remote_port = ports_by_remote.get(as_int(item.get("remote_port_id")))
        link.local_port_id = local_port.id if local_port else None
        link.remote_device_id = remote_device.id if remote_device else None
        link.remote_port_id = remote_port.id if remote_port else None
        link.remote_name = str(item.get("remote_hostname") or "")
        link.remote_port_name = str(item.get("remote_port") or "")
        link.active = bool(as_int(item.get("active")) if item.get("active") is not None else 1)
        link.last_seen_at = now
    for stale in db.scalars(
        select(NetworkLink).where(
            NetworkLink.origin != "manual", NetworkLink.source_key.not_in(seen or {"-"})
        )
    ):
        stale.active = False


def sync_cctv_device(device: Device, db: Session) -> None:
    credentials = credentials_for(device, db)
    if device.stream_url:
        result = rtsp_probe(device.stream_url, credentials)
    else:
        result = tcp_probe(device.address, 554)
        result.status = "missing_stream"
        result.reason = "Kamera terjangkau, tetapi URL stream belum dikonfigurasi"
    observation = db.scalar(
        select(DeviceObservation).where(DeviceObservation.device_id == device.id)
    )
    if observation is None:
        observation = DeviceObservation(device_id=device.id, source="rtsp")
        db.add(observation)
    observation.status = (
        "online" if result.reachable and result.status == "streaming" else "offline"
    )
    observation.stream_status = result.status
    observation.reason = result.reason[:255]
    observation.latency_ms = result.latency_ms
    observation.checked_at = utcnow()
    if result.reachable:
        device.last_seen_at = observation.checked_at
    device.monitoring_level = "stream" if device.stream_url else "basic"
    device.capabilities = {"rtsp": bool(device.stream_url), "onvif": False}


def sync_all(db: Session, client: LibreNMSClient = librenms_client) -> None:
    devices = list(
        db.scalars(select(Device).where(Device.is_active.is_(True), Device.archived_at.is_(None)))
    )
    for device in devices:
        try:
            if device.kind in NETWORK_KINDS:
                sync_network_device(device, db, client)
            elif device.kind == DeviceKind.CCTV.value:
                sync_cctv_device(device, db)
            elif device.kind == DeviceKind.HUB.value:
                device.monitoring_level = "limited"
        except (LibreNMSUnavailable, OSError, ValueError) as exc:
            observation = db.scalar(
                select(DeviceObservation).where(DeviceObservation.device_id == device.id)
            )
            if observation is None:
                observation = DeviceObservation(device_id=device.id, source="librenms")
                db.add(observation)
            observation.status = "unknown"
            observation.reason = str(exc)[:255]
            observation.checked_at = utcnow()
    if client.configured:
        try:
            sync_links(db, client)
        except LibreNMSUnavailable:
            pass
    db.commit()


def port_to_read(port: NetworkPort, expectation: PortExpectation | None) -> NetworkPortRead:
    mode = PortExpectationMode(expectation.mode) if expectation else PortExpectationMode.SPARE
    if expectation and expectation.consecutive_mismatches >= 2:
        condition = "disconnected" if mode == PortExpectationMode.REQUIRED else "unexpected_active"
    elif port.oper_status == "unknown":
        condition = "unknown"
    else:
        condition = "healthy" if port.oper_status == "up" else "normal_empty"
    utilization = None
    if port.speed_bps and (port.rx_bps is not None or port.tx_bps is not None):
        utilization = round(max(port.rx_bps or 0, port.tx_bps or 0) / port.speed_bps * 100, 2)
    return NetworkPortRead(
        id=port.id,
        device_id=port.device_id,
        source_port_id=port.source_port_id,
        if_index=port.if_index,
        name=port.name,
        description=port.description,
        alias=port.alias,
        admin_status=port.admin_status,
        oper_status=port.oper_status,
        speed_bps=port.speed_bps,
        rx_bps=port.rx_bps,
        tx_bps=port.tx_bps,
        utilization_percent=utilization,
        errors_in=port.errors_in,
        errors_out=port.errors_out,
        discards_in=port.discards_in,
        discards_out=port.discards_out,
        mac_address=port.mac_address,
        expectation=mode,
        expected_device_id=expectation.expected_device_id if expectation else None,
        expectation_label=expectation.label if expectation else "",
        condition=condition,
        last_seen_at=port.last_seen_at,
    )


def device_health(device: Device, db: Session) -> DeviceHealthRead:
    ports = list(db.scalars(select(NetworkPort).where(NetworkPort.device_id == device.id)))
    expectations = {
        item.port_id: item
        for item in db.scalars(
            select(PortExpectation).where(
                PortExpectation.port_id.in_([port.id for port in ports] or [-1])
            )
        )
    }
    port_reads = [port_to_read(port, expectations.get(port.id)) for port in ports]
    issues: list[DeviceIssue] = []
    for port in port_reads:
        if port.condition == "disconnected":
            issues.append(
                DeviceIssue(
                    code="required_port_down",
                    severity="critical",
                    title=f"{port.name} terputus",
                    detail=f"Port wajib {port.expectation_label or port.name} tidak aktif.",
                    port_id=port.id,
                )
            )
        elif port.condition == "unexpected_active":
            issues.append(
                DeviceIssue(
                    code="unexpected_port_active",
                    severity="warning",
                    title=f"Perangkat asing pada {port.name}",
                    detail="Port cadangan yang belum ditugaskan terdeteksi aktif.",
                    port_id=port.id,
                )
            )
    observation = db.scalar(
        select(DeviceObservation).where(DeviceObservation.device_id == device.id)
    )
    checked_at = observation.checked_at if observation else device.last_seen_at
    if checked_at is not None and checked_at.tzinfo is None:
        checked_at = checked_at.replace(tzinfo=UTC)
    if observation and observation.status == "offline":
        issues.append(
            DeviceIssue(
                code="network_device_down",
                severity="critical",
                title="Perangkat tidak terjangkau",
                detail=observation.reason or "Pemeriksaan koneksi perangkat gagal.",
            )
        )
    elif observation and observation.status == "unknown":
        issues.append(
            DeviceIssue(
                code="monitoring_unavailable",
                severity="warning",
                title="Mesin monitoring tidak tersedia",
                detail=observation.reason or "Kondisi perangkat belum dapat dipastikan.",
            )
        )
    if (
        device.kind == DeviceKind.CCTV.value
        and observation
        and observation.stream_status != "streaming"
    ):
        issues.append(
            DeviceIssue(
                code="cctv_stream_down",
                severity="critical",
                title="Stream CCTV tidak tersedia",
                detail=observation.reason or "Handshake stream tidak berhasil.",
            )
        )
    stale_before = utcnow() - timedelta(seconds=settings.network_stale_after_seconds)
    if device.kind in NETWORK_KINDS | {DeviceKind.CCTV.value} and (
        checked_at is None or checked_at < stale_before
    ):
        issues.append(
            DeviceIssue(
                code="monitoring_data_stale",
                severity="warning",
                title="Data monitoring terlambat",
                detail="Belum ada data baru dalam dua siklus pemeriksaan.",
            )
        )
    status = (
        "critical"
        if any(item.severity == "critical" for item in issues)
        else "warning"
        if issues
        else "healthy"
    )
    if checked_at is None and not issues:
        status = "unknown"
    return DeviceHealthRead(
        device_id=device.id,
        status=status,
        monitoring_level=device.monitoring_level,
        checked_at=checked_at,
        last_seen_at=device.last_seen_at,
        reason=observation.reason if observation else "",
        issues=issues,
        ports=port_reads,
    )
