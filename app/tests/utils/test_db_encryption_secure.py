"""
Database Encryption Tests
--------------------------
Tests for the Fernet-based encryption utility.
OWASP: Sensitive data must be encrypted at rest.
"""

from cryptography.fernet import Fernet
from app.utils.db_encryption import (
    is_encryption_enabled,
    get_key_id,
    encrypt_value,
    decrypt_value,
)


def test_encryption_disabled_by_default():
    """When encryption is explicitly disabled, encrypt_value returns input unchanged."""
    import app.utils.db_encryption as enc_module
    original_enabled = enc_module._ENCRYPTION_ENABLED
    original_fernet = enc_module._fernet
    enc_module._ENCRYPTION_ENABLED = False
    enc_module._fernet = None
    try:
        result = encrypt_value("hello")
        assert result == "hello"
    finally:
        enc_module._ENCRYPTION_ENABLED = original_enabled
        enc_module._fernet = original_fernet


def test_encrypt_value_none_returns_none():
    assert encrypt_value(None) is None


def test_decrypt_value_none_returns_none():
    assert decrypt_value(None) is None


def test_decrypt_value_passthrough_when_disabled():
    """When encryption is off, decrypt returns input unchanged."""
    result = decrypt_value("plaintext value")
    assert result == "plaintext value"


def test_get_key_id_returns_string():
    key_id = get_key_id()
    assert isinstance(key_id, str)
    assert len(key_id) > 0


def test_is_encryption_enabled_returns_bool():
    result = is_encryption_enabled()
    assert isinstance(result, bool)


def test_encrypt_decrypt_roundtrip_with_key():
    """When a valid key is provided, encrypt/decrypt must round-trip."""
    key = Fernet.generate_key().decode("utf-8")

    # Patch the module-level state
    import app.utils.db_encryption as enc_module

    original_enabled = enc_module._ENCRYPTION_ENABLED
    original_fernet = enc_module._fernet

    enc_module._ENCRYPTION_ENABLED = True
    enc_module._fernet = Fernet(key.encode("utf-8"))

    try:
        encrypted = encrypt_value("sensitive data")
        assert encrypted != "sensitive data"
        decrypted = decrypt_value(encrypted)
        assert decrypted == "sensitive data"
    finally:
        enc_module._ENCRYPTION_ENABLED = original_enabled
        enc_module._fernet = original_fernet


def test_decrypt_invalid_token_returns_original():
    """Decrypting non-ciphertext must return input, not raise."""
    import app.utils.db_encryption as enc_module
    from cryptography.fernet import Fernet

    key = Fernet.generate_key().decode("utf-8")
    original_enabled = enc_module._ENCRYPTION_ENABLED
    original_fernet = enc_module._fernet

    enc_module._ENCRYPTION_ENABLED = True
    enc_module._fernet = Fernet(key.encode("utf-8"))

    try:
        result = decrypt_value("not-a-valid-ciphertext")
        assert result == "not-a-valid-ciphertext"
    finally:
        enc_module._ENCRYPTION_ENABLED = original_enabled
        enc_module._fernet = original_fernet
