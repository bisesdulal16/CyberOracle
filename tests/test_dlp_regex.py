"""
Unit tests for dlp_regex.py
Purpose:
Verify that the regex-based DLP scanner (Week 2 deliverable) correctly identifies
and redacts sensitive data such as SSNs, credit card numbers, emails, and API keys.
"""

from app.middleware.dlp_regex import scan_text


def test_scan_text_detects_ssn():
    """The scanner should detect SSN patterns and return both redacted text and the entity name."""
    text = "My SSN is 123-45-6789."
    sanitized, entities = scan_text(text)

    # Ensure redaction occurred
    assert "SSN" in sanitized.upper()
    # Ensure the entity is recorded
    assert "ssn" in entities


def test_scan_text_detects_credit_card():
    """The scanner should detect credit card numbers."""
    text = "Card: 4111 1111 1111 1111."
    sanitized, entities = scan_text(text)

    # Check placeholder replacement
    assert "<CREDIT_CARD>" in sanitized
    # Check detection list
    assert "credit_card" in entities


def test_scan_text_detects_email():
    """The scanner must identify email addresses."""
    text = "Send to hello@example.com"
    sanitized, entities = scan_text(text)

    assert "<EMAIL>" in sanitized
    assert "email" in entities


def test_scan_text_detects_api_key():
    """The scanner should detect long API key-like strings."""
    text = "Key is ABCDEFGHIJKLMNOPQRSTUVWXYZ1234"
    sanitized, entities = scan_text(text)

    assert "<API_KEY>" in sanitized
    assert "api_key" in entities


def test_scan_text_no_detection():
    """If no sensitive data exists, the text must remain
    unchanged and no entities should be reported."""
    text = "Hello world"
    sanitized, entities = scan_text(text)

    assert sanitized == text
    assert entities == []
