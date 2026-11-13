import csv
import io
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.device import Device
from services.prometheus import prometheus_client


def _sanitize_csv_cell(value: object) -> object:
    if isinstance(value, str) and value:
        if value[0] in ("=", "+", "-", "@", "\t", "\r"):
            return f"'{value}"
    return value


def generate_status_csv(db: Session) -> tuple[str, str]:
    devices = list(db.scalars(select(Device).order_by(Device.name)))
    summary = prometheus_client.summary([device for device in devices if device.is_active])
    metric_by_id = {metric.device_id: metric for metric in summary.devices}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Nama",
            "Jenis",
            "Alamat",
            "Lokasi",
            "Status",
            "CPU (%)",
            "Memori (%)",
            "Disk (%)",
            "Aktif",
        ]
    )
    for device in devices:
        metric = metric_by_id.get(device.id)
        kind_val = device.kind.value if hasattr(device.kind, "value") else device.kind
        writer.writerow(
            [
                _sanitize_csv_cell(device.name),
                _sanitize_csv_cell(kind_val),
                _sanitize_csv_cell(device.address),
                _sanitize_csv_cell(device.location),
                metric.status if metric else "inactive",
                metric.cpu_percent if metric else "",
                metric.memory_percent if metric else "",
                metric.disk_percent if metric else "",
                "Ya" if device.is_active else "Tidak",
            ]
        )

    filename = f"status-infrastruktur-{datetime.now(UTC):%Y-%m-%d}.csv"
    return "\ufeff" + output.getvalue(), filename
