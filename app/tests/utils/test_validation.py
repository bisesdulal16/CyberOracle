from app.utils.validation import sanitize_input, is_valid_length


def test_sanitize_removes_dangerous_chars():
    text = "<script>alert('x')</script>"
    cleaned = sanitize_input(text)
    assert "<" not in cleaned
    assert ">" not in cleaned
    assert "'" not in cleaned


def test_valid_length():
    assert is_valid_length("hello")
    assert not is_valid_length("a" * 300)
