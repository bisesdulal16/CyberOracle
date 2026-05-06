"""
Logger Tests
-------------
Tests for compute_log_hash and mask_sensitive.
OWASP-ASVS 9.1.1, 9.5
"""

from app.utils.logger import compute_log_hash, secure_log


def test_compute_log_hash_returns_64_char_hex():
    h = compute_log_hash(
        endpoint="/test",
        method="POST",
        status_code=200,
        message="hello",
        event_type="ai_query",
    )
    assert isinstance(h, str)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_compute_log_hash_is_deterministic():
    h1 = compute_log_hash("/test", "GET", 200, "msg", "event")
    h2 = compute_log_hash("/test", "GET", 200, "msg", "event")
    assert h1 == h2


def test_compute_log_hash_changes_with_different_input():
    h1 = compute_log_hash("/test", "GET", 200, "msg1", "event")
    h2 = compute_log_hash("/test", "GET", 200, "msg2", "event")
    assert h1 != h2


def test_compute_log_hash_handles_none_values():
    h = compute_log_hash(
        endpoint=None,
        method=None,
        status_code=None,
        message=None,
        event_type=None,
    )
    assert isinstance(h, str)
    assert len(h) == 64


def test_secure_log_does_not_raise():
    """secure_log must not raise even with sensitive content."""
    secure_log("password=secret123 token=abc.def.ghi")


def test_secure_log_with_none_like_content():
    secure_log("normal log message with no sensitive data")
