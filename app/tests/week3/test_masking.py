"""
Secure Logging Masking Tests
-----------------------------
Verifies that mask_sensitive() correctly masks all sensitive
data types before they reach logs or the database.

OWASP-ASVS 9.1.1: Sensitive data must never appear in logs.
"""

from app.utils.logger import mask_sensitive


def test_masks_query_string_password():
    """Password in query string format must be masked."""
    text = "password=abc123&other=value"
    masked = mask_sensitive(text)
    assert "abc123" not in masked
    assert "***" in masked


def test_masks_json_password():
    """Password in JSON format must be masked."""
    text = '{"password": "supersecret", "username": "admin"}'
    masked = mask_sensitive(text)
    assert "supersecret" not in masked
    assert "***" in masked


def test_masks_ssn():
    """US Social Security Numbers must be masked."""
    text = "User SSN is 123-45-6789 please verify"
    masked = mask_sensitive(text)
    assert "123-45-6789" not in masked
    assert "***" in masked


def test_masks_bearer_token():
    """Bearer tokens in Authorization headers must be masked."""
    text = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.signature"
    masked = mask_sensitive(text)
    assert "eyJhbGciOiJIUzI1NiJ9" not in masked
    assert "***" in masked


def test_masks_api_key():
    """API keys in any format must be masked."""
    text = "api_key=ABCDEF123456789 was used in request"
    masked = mask_sensitive(text)
    assert "ABCDEF123456789" not in masked
    assert "***" in masked


def test_masks_email():
    """Email addresses must be masked."""
    text = "User email is john.doe@example.com in the system"
    masked = mask_sensitive(text)
    assert "john.doe@example.com" not in masked
    assert "***" in masked


def test_masks_credit_card():
    """Credit card numbers must be masked."""
    text = "Payment with card 4111111111111111 was processed"
    masked = mask_sensitive(text)
    assert "4111111111111111" not in masked
    assert "***" in masked


def test_masks_multiple_sensitive_fields():
    """Multiple sensitive fields in one string must all be masked."""
    text = "password=secret123 token=abc.def.ghi ssn=123-45-6789"
    masked = mask_sensitive(text)
    assert "secret123" not in masked
    assert "abc.def.ghi" not in masked
    assert "123-45-6789" not in masked


def test_safe_text_unchanged():
    """Non-sensitive text must pass through unchanged."""
    text = "User logged in successfully from IP 192.168.1.1"
    masked = mask_sensitive(text)
    assert "192.168.1.1" in masked
    assert "logged in successfully" in masked


def test_none_input_handled():
    """None input must not raise an exception."""
    result = mask_sensitive(None)
    assert result == ""


def test_non_string_handled():
    """Non-string input must be converted safely."""
    result = mask_sensitive(12345)
    assert isinstance(result, str)