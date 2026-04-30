"""
tests/test_key_rotation.py

Unit tests for scripts/key_rotation.py (PSFR7).
Tests key versioning, safe decryption, and .env update logic.
No real DB or file I/O required — all external calls are mocked.
"""

import os
import sys
from unittest.mock import patch
from cryptography.fernet import Fernet

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.key_rotation import _next_key_id, _decrypt_safe, _update_env  # noqa: E402


# ---------------------------------------------------------------------------
# _next_key_id
# ---------------------------------------------------------------------------


def test_next_key_id_v1_to_v2():
    assert _next_key_id("v1") == "v2"


def test_next_key_id_v2_to_v3():
    assert _next_key_id("v2") == "v3"


def test_next_key_id_v9_to_v10():
    assert _next_key_id("v9") == "v10"


def test_next_key_id_unexpected_format():
    result = _next_key_id("custom")
    assert "custom" in result


# ---------------------------------------------------------------------------
# _decrypt_safe
# ---------------------------------------------------------------------------


def test_decrypt_safe_valid_ciphertext():
    key = Fernet.generate_key()
    fernet = Fernet(key)
    ciphertext = fernet.encrypt(b"secret data").decode("utf-8")
    result = _decrypt_safe(fernet, ciphertext)
    assert result == "secret data"


def test_decrypt_safe_invalid_token_returns_original():
    key = Fernet.generate_key()
    fernet = Fernet(key)
    result = _decrypt_safe(fernet, "not-valid-ciphertext")
    assert result == "not-valid-ciphertext"


def test_decrypt_safe_wrong_key_returns_original():
    key1 = Fernet.generate_key()
    key2 = Fernet.generate_key()
    fernet1 = Fernet(key1)
    fernet2 = Fernet(key2)
    ciphertext = fernet1.encrypt(b"secret").decode("utf-8")
    result = _decrypt_safe(fernet2, ciphertext)
    assert result == ciphertext


def test_decrypt_safe_empty_string_returns_empty():
    key = Fernet.generate_key()
    fernet = Fernet(key)
    result = _decrypt_safe(fernet, "")
    assert result == ""


# ---------------------------------------------------------------------------
# _update_env
# ---------------------------------------------------------------------------


def test_update_env_replaces_key_and_version(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgresql://localhost/db\n"
        "DB_ENCRYPTION_KEY=oldkey123\n"
        "DB_ENCRYPTION_KEY_ID=v1\n"
        "JWT_SECRET_KEY=somesecret\n"
    )

    with patch("scripts.key_rotation.PROJECT_ROOT", str(tmp_path)):
        _update_env("newkey456", "v2")

    content = env_file.read_text()
    assert "DB_ENCRYPTION_KEY=newkey456" in content
    assert "DB_ENCRYPTION_KEY_ID=v2" in content
    assert "oldkey123" not in content
    assert "v1" not in content
    # Other vars must be untouched
    assert "DATABASE_URL=postgresql://localhost/db" in content
    assert "JWT_SECRET_KEY=somesecret" in content


def test_update_env_missing_file_does_not_crash(tmp_path):
    with patch("scripts.key_rotation.PROJECT_ROOT", str(tmp_path)):
        # No .env file in tmp_path — should print warning and return gracefully
        _update_env("newkey", "v2")


# ---------------------------------------------------------------------------
# Key generation sanity
# ---------------------------------------------------------------------------


def test_fernet_generate_key_is_valid():
    key = Fernet.generate_key()
    fernet = Fernet(key)
    token = fernet.encrypt(b"test")
    assert fernet.decrypt(token) == b"test"


def test_two_generated_keys_are_different():
    key1 = Fernet.generate_key()
    key2 = Fernet.generate_key()
    assert key1 != key2
