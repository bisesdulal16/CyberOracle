"""
DLP Regex Middleware Tests
---------------------------
Tests for the standalone regex DLP scanner.
OWASP: Sensitive data must be detected before storage.
"""

from app.middleware.dlp_regex import scan_text, REGEX_PATTERNS
import re


def test_scan_text_detects_ssn():
    sanitized, entities = scan_text("SSN: 123-45-6789")
    assert "ssn" in entities
    assert "123-45-6789" not in sanitized


def test_scan_text_detects_visa():
    sanitized, entities = scan_text("Card: 4111111111111111")
    assert "credit_card" in entities
    assert "4111111111111111" not in sanitized


def test_scan_text_detects_email():
    sanitized, entities = scan_text("Email: user@example.com")
    assert "email" in entities
    assert "user@example.com" not in sanitized


def test_scan_text_detects_api_key():
    sanitized, entities = scan_text("api_key=ABCDEFGHIJKLMNOP1234")
    assert "api_key" in entities


def test_scan_text_no_sensitive_data():
    sanitized, entities = scan_text("Hello world, nothing sensitive here.")
    assert entities == []
    assert sanitized == "Hello world, nothing sensitive here."


def test_scan_text_empty_string():
    sanitized, entities = scan_text("")
    assert entities == []


def test_scan_text_none_returns_none():
    sanitized, entities = scan_text(None)
    assert entities == []


def test_all_patterns_valid_regex():
    for name, pattern in REGEX_PATTERNS.items():
        compiled = re.compile(pattern)
        assert compiled is not None


def test_all_required_patterns_present():
    required = {"ssn", "credit_card", "email", "api_key"}
    assert required.issubset(set(REGEX_PATTERNS.keys()))


def test_scan_text_replaces_with_placeholder():
    sanitized, entities = scan_text("SSN: 123-45-6789")
    assert "<SSN>" in sanitized


def test_scan_text_multiple_entities():
    text = "SSN: 123-45-6789 and email: user@test.com"
    sanitized, entities = scan_text(text)
    assert "ssn" in entities
    assert "email" in entities
    assert "123-45-6789" not in sanitized
    assert "user@test.com" not in sanitized
