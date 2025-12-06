"""
tests/test_db_encryption.py

Unit tests for app/utils/db_encryption.py (PSFR7).

Covers:
- No-op behavior when encryption is disabled.
- Successful encrypt/decrypt cycle when enabled with a valid key.
- Graceful handling of invalid key configuration.
- Graceful handling of non-decryptable input.
"""

import importlib

from cryptography.fernet import Fernet


def _reload_module(monkeypatch, enabled: str, key: str | None, key_id: str = "v1"):
    """
    Helper to reload app.utils.db_encryption with fresh environment settings.

    We have to reload the module because it reads environment variables
    at import time to configure the internal Fernet instance.
    """
    from app.utils import db_encryption as db_enc_module

    # Clear existing env vars first
    monkeypatch.delenv("DB_ENCRYPTION_ENABLED", raising=False)
    monkeypatch.delenv("DB_ENCRYPTION_KEY", raising=False)
    monkeypatch.delenv("DB_ENCRYPTION_KEY_ID", raising=False)

    monkeypatch.setenv("DB_ENCRYPTION_ENABLED", enabled)
    monkeypatch.setenv("DB_ENCRYPTION_KEY_ID", key_id)
    if key is not None:
        monkeypatch.setenv("DB_ENCRYPTION_KEY", key)

    # Reload module so it re-reads the env vars
    importlib.reload(db_enc_module)
    return db_enc_module


def test_encryption_disabled_is_noop(monkeypatch):
    """
    When DB_ENCRYPTION_ENABLED=false, encryption helpers should behave as a NO-OP.

    This ensures that enabling the module in the codebase does not change
    behavior for existing tests or local development unless explicitly turned on.
    """
    db_enc_module = _reload_module(monkeypatch, enabled="false", key=None)

    assert db_enc_module.is_encryption_enabled() is False

    original = "hello world"
    encrypted = db_enc_module.encrypt_value(original)
    decrypted = db_enc_module.decrypt_value(original)

    # No-op behavior: values are returned unchanged.
    assert encrypted == original
    assert decrypted == original


def test_encrypt_decrypt_with_valid_key(monkeypatch):
    """
    When DB_ENCRYPTION_ENABLED=true and a valid Fernet key is configured,
    encrypt_value() should return ciphertext and decrypt_value() should
    return the original plaintext.
    """
    # Generate a valid Fernet key just for this test
    key = Fernet.generate_key().decode("utf-8")

    db_enc_module = _reload_module(monkeypatch, enabled="true", key=key, key_id="v1")

    assert db_enc_module.is_encryption_enabled() is True
    assert db_enc_module.get_key_id() == "v1"

    original = "sensitive log message"
    encrypted = db_enc_module.encrypt_value(original)

    # Encrypted form should be different and non-empty
    assert isinstance(encrypted, str)
    assert encrypted != original
    assert encrypted.strip() != ""

    # Decrypt back to original
    decrypted = db_enc_module.decrypt_value(encrypted)
    assert decrypted == original


def test_invalid_key_disables_encryption(monkeypatch):
    """
    If DB_ENCRYPTION_ENABLED=true but DB_ENCRYPTION_KEY is invalid,
    the module should disable encryption gracefully instead of crashing.
    """
    # This is not a valid Fernet key
    bad_key = "not-a-valid-fernet-key"

    db_enc_module = _reload_module(monkeypatch, enabled="true", key=bad_key)

    # Module should have fallen back to "disabled"
    assert db_enc_module.is_encryption_enabled() is False

    original = "hello"
    encrypted = db_enc_module.encrypt_value(original)
    assert encrypted == original  # still a no-op


def test_decrypt_non_ciphertext_returns_original(monkeypatch):
    """
    When encryption is enabled but decrypt_value() receives a string that
    is not valid ciphertext, it should return the input unchanged.

    This allows the database to contain a mix of plaintext and ciphertext
    rows during migrations or key rotation without raising errors.
    """
    key = Fernet.generate_key().decode("utf-8")
    db_enc_module = _reload_module(monkeypatch, enabled="true", key=key)

    assert db_enc_module.is_encryption_enabled() is True

    # This is not a valid Fernet token
    not_ciphertext = "just a normal string"

    result = db_enc_module.decrypt_value(not_ciphertext)
    assert result == not_ciphertext
