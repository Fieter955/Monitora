import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["APP_ENV"] = "test"
os.environ["ALLOWED_HOSTS"] = "testserver,localhost,backend"
os.environ["APP_SECRET_KEY"] = "test-secret-key-with-more-than-32-characters"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import User, UserRole
from app.security import hash_password


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.add_all(
            [
                User(
                    username="admin",
                    full_name="Admin Test",
                    password_hash=hash_password("admin-password"),
                    role=UserRole.ADMIN.value,
                ),
                User(
                    username="viewer",
                    full_name="Viewer Test",
                    password_hash=hash_password("viewer-password"),
                    role=UserRole.VIEWER.value,
                ),
            ]
        )
        db.commit()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_client(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin-password"},
    )
    assert response.status_code == 200
    return client


@pytest.fixture
def viewer_client(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "viewer", "password": "viewer-password"},
    )
    assert response.status_code == 200
    return client
