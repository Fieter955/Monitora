import logging
import time

from app.config import settings
from app.database import SessionLocal
from app.network_service import sync_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("network-sync")


def run() -> None:
    while True:
        started = time.monotonic()
        try:
            with SessionLocal() as db:
                sync_all(db)
        except Exception:
            logger.exception("Sinkronisasi monitoring gagal")
        elapsed = time.monotonic() - started
        time.sleep(max(1, settings.network_sync_interval_seconds - elapsed))


if __name__ == "__main__":
    run()
