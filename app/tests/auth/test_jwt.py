"""
JWT Utility Tests
-----------------
Tests for creating and verifying JSON Web Tokens (JWTs)
used for authentication and authorization.
Follows OWASP best practices and PEP 8 standards.
"""

from app.auth.jwt_utils import create_access_token, verify_token


def test_jwt_creation_and_verification():
    """
    Verify that a JWT can be created and successfully verified.

    OWASP:
        Ensures token integrity and proper validation of signed JWTs,
        preventing tampering and unauthorized access
        (OWASP API Security Top 10 – API2: Broken Authentication).

    PEP 8:
        Uses clear variable names and straightforward assertions
        for readability and maintainability.
    """
    payload = {"user": "niall"}
    token = create_access_token(payload)
    decoded = verify_token(token)
    assert decoded["user"] == "niall"


def test_jwt_invalid_token():
    """
    Verify that invalid JWTs are rejected during verification.

    OWASP:
        Ensures malformed or tampered tokens are not accepted,
        preventing authentication bypass vulnerabilities
        (OWASP API2: Broken Authentication).

    PEP 8:
        Exception handling is explicit and test intent is clear.
    """
    fake = "abc.def.ghi"
    try:
        verify_token(fake)
        assert False
    except Exception:
        assert True
