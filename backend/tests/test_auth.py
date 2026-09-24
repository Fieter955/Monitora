def test_login_sets_session_and_returns_current_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin-password"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert response.cookies.get("access_token")
    assert client.get("/api/v1/auth/me").json()["username"] == "admin"


def test_invalid_login_is_rejected(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "incorrect-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Nama pengguna atau kata sandi salah"


def test_protected_endpoint_requires_session(client):
    response = client.get("/api/v1/devices")
    assert response.status_code == 401


def test_internal_admin_authorization_accepts_admin(admin_client):
    response = admin_client.get("/internal/auth/admin")
    assert response.status_code == 204
    assert response.content == b""


def test_internal_admin_authorization_rejects_viewer(viewer_client):
    response = viewer_client.get("/internal/auth/admin")
    assert response.status_code == 403
    assert response.json()["detail"] == "Akses administrator diperlukan"


def test_internal_admin_authorization_requires_session(client):
    response = client.get("/internal/auth/admin")
    assert response.status_code == 401
    assert response.json()["detail"] == "Sesi tidak valid"


def test_internal_session_authorization_accepts_admin(admin_client):
    response = admin_client.get("/internal/auth/session")
    assert response.status_code == 204
    assert response.content == b""


def test_internal_session_authorization_accepts_viewer(viewer_client):
    response = viewer_client.get("/internal/auth/session")
    assert response.status_code == 204
    assert response.content == b""


def test_internal_session_authorization_requires_session(client):
    response = client.get("/internal/auth/session")
    assert response.status_code == 401
    assert response.json()["detail"] == "Sesi tidak valid"
