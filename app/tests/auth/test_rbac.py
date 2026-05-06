import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

import app.auth.rbac as rbac


# --------------------------------------------------
# Helper for creating fake Authorization credentials
# --------------------------------------------------


def make_credentials(token="fake_token"):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


# ==================================================
# require_roles() tests
# ==================================================


@pytest.mark.asyncio
async def test_require_roles_success(monkeypatch):
    """Valid token with correct role"""

    monkeypatch.setattr(rbac, "verify_token", lambda token: {"role": "admin"})

    dependency = rbac.require_roles("admin")

    result = await dependency(credentials=make_credentials())

    assert result["role"] == "admin"


@pytest.mark.asyncio
async def test_require_roles_missing_token():
    """No Authorization header should return 401"""

    dependency = rbac.require_roles("admin")

    with pytest.raises(HTTPException) as exc:
        await dependency(credentials=None)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_require_roles_invalid_token(monkeypatch):
    """Invalid JWT should return 401"""

    def bad_token(token):
        raise ValueError()

    monkeypatch.setattr(rbac, "verify_token", bad_token)

    dependency = rbac.require_roles("admin")

    with pytest.raises(HTTPException) as exc:
        await dependency(credentials=make_credentials())

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_require_roles_forbidden(monkeypatch):
    """Valid token but wrong role"""

    monkeypatch.setattr(rbac, "verify_token", lambda token: {"role": "auditor"})

    dependency = rbac.require_roles("admin")

    with pytest.raises(HTTPException) as exc:
        await dependency(credentials=make_credentials())

    assert exc.value.status_code == 403


# ==================================================
# require_permission() tests
# ==================================================


@pytest.mark.asyncio
async def test_permission_missing_token():
    """No token provided"""

    dependency = rbac.require_permission("logs.read")

    with pytest.raises(HTTPException) as exc:
        await dependency(credentials=None)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_permission_invalid_token(monkeypatch):
    """JWT verification fails"""

    def bad_token(token):
        raise ValueError()

    monkeypatch.setattr(rbac, "verify_token", bad_token)

    dependency = rbac.require_permission("logs.read")

    with pytest.raises(HTTPException) as exc:
        await dependency(credentials=make_credentials())

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_permission_missing_role(monkeypatch):
    """JWT has no role claim"""

    monkeypatch.setattr(rbac, "verify_token", lambda token: {})

    monkeypatch.setattr(rbac, "get_role_permissions", lambda role: [])

    dependency = rbac.require_permission("logs.read")

    with pytest.raises(HTTPException) as exc:
        await dependency(credentials=make_credentials())

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_permission_denied(monkeypatch):
    """Role exists but permission not granted"""

    monkeypatch.setattr(rbac, "verify_token", lambda token: {"role": "auditor"})

    monkeypatch.setattr(rbac, "get_role_permissions", lambda role: ["logs.read"])

    dependency = rbac.require_permission("documents.scan")

    with pytest.raises(HTTPException) as exc:
        await dependency(credentials=make_credentials())

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_permission_allowed(monkeypatch):
    """Role has required permission"""

    monkeypatch.setattr(rbac, "verify_token", lambda token: {"role": "developer"})

    monkeypatch.setattr(rbac, "get_role_permissions", lambda role: ["documents.scan"])

    dependency = rbac.require_permission("documents.scan")

    result = await dependency(credentials=make_credentials())

    assert result["role"] == "developer"


@pytest.mark.asyncio
async def test_admin_override(monkeypatch):
    """Admin override using access_all_endpoints"""

    monkeypatch.setattr(rbac, "verify_token", lambda token: {"role": "admin"})

    monkeypatch.setattr(
        rbac, "get_role_permissions", lambda role: ["access_all_endpoints"]
    )

    dependency = rbac.require_permission("any_permission")

    result = await dependency(credentials=make_credentials())

    assert result["role"] == "admin"
