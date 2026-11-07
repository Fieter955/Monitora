from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.config import settings

engine_options: dict = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}
    if settings.database_url.endswith(":memory:"):
        engine_options["poolclass"] = StaticPool

engine = create_engine(settings.database_url, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
