"""
Database Encryption Utilities (PSFR7)
====================================
Provides OPTIONAL application-level encryption for values before they are
stored in the database.

Goals for CyberOracle:
- Do NOT break existing behavior when encryption is disabled.
- Allow encryption to be turned on/off via environment variables.
- Centralize key handling so future Vault/KMS integration is easy.

We use Fernet (symmetric AES-based encryption) from the `cryptography`
package. Ciphertexts are base64-encoded strings that fit in normal TEXT
columns in Postgres.
"""

import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

# -------------------------------------------------------------------------
# Configuration (loaded from environment)
# -------------------------------------------------------------------------

# Feature flag: enables/disables encryption without code changes.
_ENCRYPTION_ENABLED = os.getenv("DB_ENCRYPTION_ENABLED", "false").lower() == "true"

# Symmetric key material (Fernet-compatible base64 string).
# In a real deployment this should come from a secret manager, not hard-coded.
_ENCRYPTION_KEY = os.getenv("DB_ENCRYPTION_KEY")

# Logical key identifier (for future key rotation, e.g. "v1", "v2").
_ENCRYPTION_KEY_ID = os.getenv("DB_ENCRYPTION_KEY_ID", "v1")

_fernet: Optional[Fernet] = None

if _ENCRYPTION_ENABLED and _ENCRYPTION_KEY:
    try:
        # Expect a Fernet-compatible key (url-safe base64).
        _fernet = Fernet(_ENCRYPTION_KEY.encode("utf-8"))
    except Exception:
        # If key is invalid, disable encryption gracefully so we do not
        # crash the whole application because of misconfiguration.
        _fernet = None
        _ENCRYPTION_ENABLED = False


# -------------------------------------------------------------------------
# Public helper functions
# -------------------------------------------------------------------------


def is_encryption_enabled() -> bool:
    """
    Returns True if database encryption is active AND a valid key is loaded.

    This can be used by other parts of the system (health checks, admin
    endpoints, etc.) to report whether encryption is currently in effect.
    """
    return _ENCRYPTION_ENABLED and _fernet is not None


def get_key_id() -> str:
    """
    Returns the logical key identifier (e.g. "v1", "v2").

    This does not affect the cryptography itself, but is useful for:
    - tagging records with which key version was used
    - planning and documenting key rotation strategies
    """
    return _ENCRYPTION_KEY_ID


def encrypt_value(value: Optional[str]) -> Optional[str]:
    """
    Encrypt a string value if encryption is enabled.

    Behavior:
    - If value is None -> returns None.
    - If encryption is disabled or misconfigured -> returns the input unchanged.
    - If enabled and a valid key is present -> returns a base64 ciphertext string.

    This design makes it safe to call encrypt_value(...) from anywhere in
    the codebase without worrying about breaking tests or local dev when
    encryption is turned off.
    """
    if value is None:
        return None

    if not is_encryption_enabled():
        # No-op when disabled; preserves existing behavior.
        return value

    assert _fernet is not None
    token = _fernet.encrypt(value.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_value(value: Optional[str]) -> Optional[str]:
    """
    Attempt to decrypt a string value if encryption is enabled.

    Behavior:
    - If encryption is disabled -> returns the input unchanged.
    - If the value is valid ciphertext -> returns decrypted plaintext.
    - If the value is not decryptable (e.g. old plaintext from before
      encryption was enabled, or encrypted with a different key) ->
      returns the input unchanged instead of raising an error.

    This tolerant behavior allows the database to contain a mix of
    plaintext and ciphertext rows during migrations or key rotation.
    """
    if value is None:
        return None

    if not is_encryption_enabled():
        return value

    assert _fernet is not None
    try:
        plain = _fernet.decrypt(value.encode("utf-8"))
        return plain.decode("utf-8")
    except (InvalidToken, ValueError, TypeError):
        # Either this was not encrypted with the current key, or it is
        # simply a legacy plaintext value. In both cases we safely
        # return the original input.
        return value
