"""
Permissions Policy Tests
"""

from app.auth.permissions import ROLE_PERMISSIONS


def test_admin_has_all_permissions():
    perms = ROLE_PERMISSIONS["admin"]
    assert "ai.query" in perms
    assert "logs.read" in perms
    assert "reports.read" in perms


def test_auditor_cannot_query_ai():
    assert "ai.query" not in ROLE_PERMISSIONS["auditor"]


def test_developer_can_query_ai():
    assert "ai.query" in ROLE_PERMISSIONS["developer"]


def test_all_roles_defined():
    assert "admin" in ROLE_PERMISSIONS
    assert "developer" in ROLE_PERMISSIONS
    assert "auditor" in ROLE_PERMISSIONS
