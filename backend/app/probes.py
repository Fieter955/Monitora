import base64
import socket
import time
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class ProbeResult:
    reachable: bool
    status: str
    reason: str
    latency_ms: float | None = None


def tcp_probe(address: str, port: int, timeout: float = 3.0) -> ProbeResult:
    started = time.perf_counter()
    try:
        with socket.create_connection((address, port), timeout=timeout):
            latency = (time.perf_counter() - started) * 1000
            return ProbeResult(True, "online", "Koneksi TCP berhasil", round(latency, 2))
    except OSError as exc:
        return ProbeResult(False, "offline", f"Koneksi gagal: {exc}")


def rtsp_probe(
    stream_url: str,
    credentials: dict[str, str] | None = None,
    timeout: float = 4.0,
) -> ProbeResult:
    parsed = urlparse(stream_url)
    if parsed.scheme.lower() != "rtsp" or not parsed.hostname:
        return ProbeResult(False, "invalid", "URL stream harus memakai skema rtsp://")
    port = parsed.port or 554
    started = time.perf_counter()
    try:
        with socket.create_connection((parsed.hostname, port), timeout=timeout) as connection:
            connection.settimeout(timeout)
            headers = [
                f"OPTIONS {stream_url} RTSP/1.0",
                "CSeq: 1",
                "User-Agent: Pantau-Infrastruktur/1.0",
            ]
            username = (credentials or {}).get("username")
            password = (credentials or {}).get("password")
            if username and password:
                token = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers.append(f"Authorization: Basic {token}")
            connection.sendall(("\r\n".join(headers) + "\r\n\r\n").encode())
            response = connection.recv(1024).decode("latin-1", errors="replace")
        latency = round((time.perf_counter() - started) * 1000, 2)
    except OSError as exc:
        return ProbeResult(False, "offline", f"Stream tidak dapat dijangkau: {exc}")

    first_line = response.splitlines()[0] if response else ""
    if " 200 " in first_line:
        return ProbeResult(True, "streaming", "Handshake RTSP berhasil", latency)
    if " 401 " in first_line:
        return ProbeResult(
            True, "auth_failed", "Kamera terjangkau tetapi autentikasi ditolak", latency
        )
    return ProbeResult(
        True, "stream_error", f"Respons RTSP tidak sehat: {first_line or 'kosong'}", latency
    )
