"""
API Key Utility Tests
---------------------
Tests for generating and validating API keys used
for authentication in secure systems.
Follows OWASP best practices and PEP 8 standards.
"""

from app.auth.api_key_utils import generate_api_key, validate_api_key


def test_generate_api_key_length():
    """
    Verify that generated API keys meet expected length requirements.

    OWASP:
        Ensures sufficient entropy in API keys to resist brute-force attacks
        (OWASP API Security Top 10 – API2: Broken Authentication).

    PEP 8:
        Test name is descriptive and uses lowercase with underscores.
    """
    key = generate_api_key()
    assert len(key) == 64  # 32 bytes hex → 64 chars


def test_validate_api_key_success():
    """
    Verify that identical API keys are successfully validated.

    OWASP:
        Confirms correct authentication behavior when valid credentials are used,
        preventing false negatives.

    PEP 8:
        Simple and readable assertion structure.
    """
    key = generate_api_key()
    assert validate_api_key(key, key) is True


def test_validate_api_key_failure():
    """
    Verify that different API keys fail validation.

    OWASP:
        Prevents authentication bypass by ensuring mismatched keys are rejected
        (OWASP API2: Broken Authentication).

    PEP 8:
        Consistent variable naming and clear test intent.
    """
    key1 = generate_api_key()
    key2 = generate_api_key()
    assert validate_api_key(key1, key2) is False
