"""
JWT Utility Tests
-----------------
Tests for creating and verifying JSON Web Tokens (JWTs).
Follows OWASP best practices and PEP 8 standards.

OWASP API2: Broken Authentication
PEP 8: descriptive names, pytest.raises idiom throughout
"""

import pytest
from app.auth.jwt_utils import create_access_token, verify_token


def test_jwt_valid_rbac_payload():
    """
    Token with correct sub and role claims should decode successfully.

    OWASP API2: Confirms tokens with proper RBAC claims are accepted.
    """
    payload = {"sub": "niall", "role": "developer"}
    token = create_access_token(payload)
    decoded = verify_token(token)
    assert decoded["sub"] == "niall"
    assert decoded["role"] == "developer"


def test_jwt_invalid_token():
    """
    Malformed tokens must be rejected.
    OWASP API2: Prevents authentication bypass via token tampering.
    """
    with pytest.raises(Exception):
        verify_token("abc.def.ghi")


def test_jwt_missing_role_raises():
    """
    Tokens without a role claim must be rejected.
    RBAC depends on the role claim being present in every token.
    """
    token = create_access_token({"sub": "niall"})
    with pytest.raises(ValueError):
        verify_token(token)


def test_jwt_missing_sub_raises():
    """
    Tokens without a subject claim must be rejected.
    OWASP API2: Subject claim identifies the authenticated principal.
    """
    token = create_access_token({"role": "developer"})
    with pytest.raises(ValueError):
        verify_token(token)


def test_jwt_contains_expiry_and_iat():
    """
    All tokens must contain expiration and issued-at claims.
    OWASP API2: Prevents tokens from being valid indefinitely.
    """
    payload = {"sub": "niall", "role": "developer"}
    token = create_access_token(payload)
    decoded = verify_token(token)
    assert "exp" in decoded
    assert "iat" in decoded


def test_jwt_all_roles_preserved():
    """
    All three system roles must survive encode/decode correctly.
    Ensures RBAC enforcement works for every role in the system.
    """
    for role in ["admin", "developer", "auditor"]:
        token = create_access_token({"sub": "testuser", "role": role})
        decoded = verify_token(token)
        assert decoded["role"] == role
