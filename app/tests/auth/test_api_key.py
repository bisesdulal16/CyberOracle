"""
API Key Utility Tests
---------------------
Tests for generating and validating API keys
used for machine-to-machine authentication.

OWASP API2: Broken Authentication
PEP 8: descriptive names, pytest idioms throughout
"""

import inspect
import app.auth.api_key_utils as mod
from app.auth.api_key_utils import generate_api_key, validate_api_key


def test_generate_api_key_length():
    """
    Keys must be 64 hex characters (32 bytes) for sufficient entropy.
    OWASP API2: Short keys are vulnerable to brute force attacks.
    """
    key = generate_api_key()
    assert len(key) == 64


def test_validate_api_key_success():
    """
    Matching keys must validate successfully.
    """
    key = generate_api_key()
    assert validate_api_key(key, key) is True


def test_validate_api_key_failure():
    """
    Non-matching keys must be rejected.
    OWASP API2: Prevents authentication bypass via key guessing.
    """
    key1 = generate_api_key()
    key2 = generate_api_key()
    assert validate_api_key(key1, key2) is False


def test_api_keys_are_unique():
    """
    Every generated key must be unique.
    OWASP API2: Predictable keys are a critical vulnerability.
    """
    keys = {generate_api_key() for _ in range(10)}
    assert len(keys) == 10


def test_api_key_uses_timing_safe_comparison():
    """
    Validation must use compare_digest not == operator.
    OWASP API2: == is vulnerable to timing attacks.
    """
    src = inspect.getsource(mod.validate_api_key)
    assert "compare_digest" in src
