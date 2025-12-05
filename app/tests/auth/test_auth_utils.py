# app/tests/auth/test_auth_utils.py
from datetime import timedelta
from jose import jwt

from app.auth.auth_utils import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    SECRET_KEY,
    ALGORITHM,
)


def test_hash_password_creates_valid_hash():
    password = "TestPassword123!"
    hashed = hash_password(password)

    assert hashed != password  # should not match plain
    assert hashed.startswith("$2b$")  # bcrypt hash prefix


def test_verify_password_success():
    password = "MySecurePass!"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_failure():
    correct = "CorrectPassword!"
    wrong = "WrongPassword!"
    hashed = hash_password(correct)

    assert verify_password(wrong, hashed) is False


def test_create_access_token_contains_expected_claims():
    data = {"sub": "testuser"}
    token = create_access_token(data)

    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert decoded["sub"] == "testuser"
    assert "exp" in decoded  # expiration included


def test_create_access_token_custom_expiry():
    data = {"sub": "tester"}
    delta = timedelta(minutes=5)

    token = create_access_token(data, expires_delta=delta)
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    # expiration should be roughly now + 5 minutes
    assert decoded["exp"] is not None


def test_verify_token_success():
    data = {"sub": "verify_test"}
    token = create_access_token(data)

    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "verify_test"


def test_verify_token_failure_bad_signature():
    # Tamper token → should return None
    data = {"sub": "tamper"}
    token = create_access_token(data)

    tampered = token + "xyz"  # invalid token
    assert verify_token(tampered) is None


def test_verify_token_failure_wrong_secret(monkeypatch):
    data = {"sub": "wrongsecret"}
    token = create_access_token(data)

    # monkeypatch SECRET_KEY used inside verify_token
    monkeypatch.setattr("app.auth.auth_utils.SECRET_KEY", "wrong")

    assert verify_token(token) is None
