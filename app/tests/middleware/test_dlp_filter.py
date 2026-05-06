"""
DLP Filter Middleware Tests
----------------------------
Tests for the DLP sanitization helper functions.
"""

from app.middleware.dlp_filter import _sanitize_value


def test_sanitize_string_with_ssn():
    detected = set()
    result = _sanitize_value("My SSN is 123-45-6789", detected)
    assert isinstance(result, str)
    assert "123-45-6789" not in result


def test_sanitize_clean_string():
    detected = set()
    result = _sanitize_value("Hello world", detected)
    assert result == "Hello world"
    assert len(detected) == 0


def test_sanitize_dict_recursively():
    detected = set()
    payload = {"name": "John", "ssn": "123-45-6789"}
    result = _sanitize_value(payload, detected)
    assert isinstance(result, dict)
    assert "123-45-6789" not in str(result)


def test_sanitize_list_recursively():
    detected = set()
    payload = ["hello", "My SSN is 123-45-6789"]
    result = _sanitize_value(payload, detected)
    assert isinstance(result, list)
    assert "123-45-6789" not in str(result)


def test_sanitize_non_string_passthrough():
    detected = set()
    result = _sanitize_value(12345, detected)
    assert result == 12345


def test_sanitize_none_passthrough():
    detected = set()
    result = _sanitize_value(None, detected)
    assert result is None


def test_sanitize_bool_passthrough():
    detected = set()
    result = _sanitize_value(True, detected)
    assert result is True


def test_sanitize_nested_dict():
    detected = set()
    payload = {"user": {"email": "test@example.com"}}
    result = _sanitize_value(payload, detected)
    assert isinstance(result, dict)
