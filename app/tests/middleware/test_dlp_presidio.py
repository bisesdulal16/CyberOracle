"""
DLP Presidio Tests
-------------------
Tests for the Presidio-based PII scanner.
"""

from app.middleware.dlp_presidio import presidio_scan


def test_presidio_scan_clean_text():
    text, entities = presidio_scan("Hello world", alert=False)
    assert isinstance(text, str)
    assert isinstance(entities, list)


def test_presidio_scan_detects_email():
    text, entities = presidio_scan("Contact user@example.com", alert=False)
    assert any("EMAIL" in e for e in entities)
    assert "user@example.com" not in text


def test_presidio_scan_detects_ssn():
    text, entities = presidio_scan("SSN is 123-45-6789", alert=False)
    assert len(entities) > 0
    assert "123-45-6789" not in text


def test_presidio_scan_returns_tuple():
    result = presidio_scan("test", alert=False)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_presidio_scan_empty_string():
    text, entities = presidio_scan("", alert=False)
    assert isinstance(text, str)
    assert entities == []
