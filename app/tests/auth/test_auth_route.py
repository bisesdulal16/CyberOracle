"""
Auth Route Tests
-----------------
Tests for login endpoint and user store.
Uses JWT token creation directly to avoid bcrypt in CI.
"""

from app.routes.auth import _build_user_store
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_build_user_store_returns_dict():
    store = _build_user_store()
    assert isinstance(store, dict)


def test_build_user_store_has_three_users():
    store = _build_user_store()
    assert len(store) == 3


def test_build_user_store_has_admin():
    store = _build_user_store()
    roles = [v[1] for v in store.values()]
    assert "admin" in roles


def test_build_user_store_has_developer():
    store = _build_user_store()
    roles = [v[1] for v in store.values()]
    assert "developer" in roles


def test_build_user_store_has_auditor():
    store = _build_user_store()
    roles = [v[1] for v in store.values()]
    assert "auditor" in roles


def test_login_wrong_password_returns_401():
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "definitelywrong"},
    )
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


def test_login_unknown_user_returns_401():
    response = client.post(
        "/auth/login",
        json={"username": "nobody", "password": "anything"},
    )
    assert response.status_code == 401


def test_login_success_returns_access_token():
    """Login with correct credentials returns a JWT token."""
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "changeme_admin"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "admin"


def test_login_developer_success():
    response = client.post(
        "/auth/login",
        json={"username": "developer", "password": "changeme_dev"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "developer"


def test_login_auditor_success():
    response = client.post(
        "/auth/login",
        json={"username": "auditor", "password": "changeme_auditor"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "auditor"
