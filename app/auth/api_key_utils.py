"""
API Key Utilities
-----------------
Responsible for generating and validating API keys used
to authenticate machine-to-machine or internal traffic.
Follows OWASP ASVS recommendations for key randomness.
"""

import secrets
from app.utils.logger import record_auth_failure


def generate_api_key(length: int = 32) -> str:
    """
    Generate a cryptographically secure API key.
    Uses Python's secrets module for strong randomness.
    """
    return secrets.token_hex(length)


def validate_api_key(provided_key: str, stored_key: str) -> bool:
    """
    Safely compare API keys to avoid timing attacks.
    Returns True if keys match exactly.
    """
    is_valid = secrets.compare_digest(provided_key, stored_key)

    if not is_valid:
        # We do NOT log the key itself (OWASP), just a generic auth failure
        record_auth_failure(username="api_key_client")

    return is_valid
