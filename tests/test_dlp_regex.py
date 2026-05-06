"""
Unit tests for dlp_regex.py
Purpose:
Verify that the regex-based DLP scanner correctly identifies
and redacts sensitive data — SSNs, credit cards, emails, API keys.

OWASP API Security: Sensitive data must be detected and redacted
before storage or transmission.
"""

from app.middleware.dlp_regex import scan_text, REGEX_PATTERNS
import re


# ---------------------------------------------------------------------------
# SSN tests
# ---------------------------------------------------------------------------


def test_scan_text_detects_ssn():
    """Standard SSN format XXX-XX-XXXX must be detected."""
    text = "My SSN is 123-45-6789."
    sanitized, entities = scan_text(text)
    assert "<SSN>" in sanitized
    assert "ssn" in entities
    assert "123-45-6789" not in sanitized


def test_scan_text_ssn_not_in_output():
    """Raw SSN must not appear in sanitized output."""
    text = "SSN: 987-65-4321"
    sanitized, _ = scan_text(text)
    assert "987-65-4321" not in sanitized


# ---------------------------------------------------------------------------
# Credit card tests
# ---------------------------------------------------------------------------


def test_scan_text_detects_visa():
    """Visa card number must be detected and redacted."""
    text = "Card: 4111111111111111"
    sanitized, entities = scan_text(text)
    assert "<CREDIT_CARD>" in sanitized
    assert "credit_card" in entities
    assert "4111111111111111" not in sanitized


def test_scan_text_detects_mastercard():
    """Mastercard number must be detected."""
    text = "Pay with 5500005555555559"
    sanitized, entities = scan_text(text)
    assert "<CREDIT_CARD>" in sanitized
    assert "credit_card" in entities


def test_scan_text_detects_amex():
    """American Express card number must be detected."""
    text = "Amex: 378282246310005"
    sanitized, entities = scan_text(text)
    assert "<CREDIT_CARD>" in sanitized
    assert "credit_card" in entities


# ---------------------------------------------------------------------------
# Email tests
# ---------------------------------------------------------------------------


def test_scan_text_detects_email():
    """Standard email addresses must be detected."""
    text = "Send to hello@example.com"
    sanitized, entities = scan_text(text)
    assert "<EMAIL>" in sanitized
    assert "email" in entities
    assert "hello@example.com" not in sanitized


def test_scan_text_detects_university_email():
    """University email addresses must be detected."""
    text = "Contact student@unt.edu for info"
    sanitized, entities = scan_text(text)
    assert "<EMAIL>" in sanitized
    assert "email" in entities


# ---------------------------------------------------------------------------
# API key tests
# ---------------------------------------------------------------------------


def test_scan_text_detects_api_key_format():
    """API key in key=value format must be detected."""
    text = "api_key=ABCDEFGHIJKLMNOP1234"
    sanitized, entities = scan_text(text)
    assert "api_key" in entities
    assert "ABCDEFGHIJKLMNOP1234" not in sanitized


def test_scan_text_detects_aws_key():
    """AWS access key format must be detected."""
    text = "AWS key: AKIAIOSFODNN7EXAMPLE"
    sanitized, entities = scan_text(text)
    assert "api_key" in entities


def test_scan_text_detects_sk_prefix_key():
    """sk- prefixed keys (OpenAI style) must be detected."""
    text = "key = sk-abcdefghijklmnopqrstuvwx"
    sanitized, entities = scan_text(text)
    assert "api_key" in entities


# ---------------------------------------------------------------------------
# No detection tests
# ---------------------------------------------------------------------------


def test_scan_text_no_detection():
    """Safe text must pass through unchanged."""
    text = "Hello world, this is a normal sentence."
    sanitized, entities = scan_text(text)
    assert sanitized == text
    assert entities == []


def test_scan_text_short_numbers_not_flagged():
    """Short digit sequences must not be flagged as credit cards."""
    text = "Call us at 555-1234 or visit room 404"
    sanitized, entities = scan_text(text)
    assert "credit_card" not in entities


def test_scan_text_plain_long_word_not_flagged():
    """Long alphanumeric words without key prefix must not be flagged as API keys."""
    text = "The word internationalization has many letters"
    sanitized, entities = scan_text(text)
    assert "api_key" not in entities


# ---------------------------------------------------------------------------
# Multiple entities
# ---------------------------------------------------------------------------


def test_scan_text_detects_multiple_entities():
    """Multiple sensitive entities in one string must all be detected."""
    text = "SSN: 123-45-6789, email: user@test.com, card: 4111111111111111"
    sanitized, entities = scan_text(text)
    assert "ssn" in entities
    assert "email" in entities
    assert "credit_card" in entities
    assert "123-45-6789" not in sanitized
    assert "user@test.com" not in sanitized
    assert "4111111111111111" not in sanitized


# ---------------------------------------------------------------------------
# Pattern existence test
# ---------------------------------------------------------------------------


def test_all_required_patterns_exist():
    """All required DLP patterns must be defined."""
    required = {"ssn", "credit_card", "email", "api_key"}
    assert required.issubset(set(REGEX_PATTERNS.keys()))


def test_all_patterns_are_valid_regex():
    """All DLP patterns must be valid regular expressions."""
    for name, pattern in REGEX_PATTERNS.items():
        try:
            re.compile(pattern)
        except re.error as e:
            assert False, f"Pattern '{name}' is invalid regex: {e}"
