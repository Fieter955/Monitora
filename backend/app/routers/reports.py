import csv
import io
from datetime import UTC, datetime

from fastapi import APIRouter, Response
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession
from app.models import Device
from app.prometheus import prometheus_client

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/status.csv")
def status_report(db: DbSession, _: CurrentUser) -> Response:
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
        writer.writerow(
            [
                device.name,
                device.kind,
                device.address,
                device.location,
                metric.status if metric else "inactive",
                metric.cpu_percent if metric else "",
                metric.memory_percent if metric else "",
                metric.disk_percent if metric else "",
                "Ya" if device.is_active else "Tidak",
            ]
        )

    filename = f"status-infrastruktur-{datetime.now(UTC):%Y-%m-%d}.csv"
    return Response(
        content="\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
