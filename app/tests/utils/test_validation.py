from app.utils.validation import validate_text_field


def test_validation_pass():
    assert validate_text_field({"text": "hello"}) is True


def test_validation_fail_missing_key():
    assert validate_text_field({}) is False


def test_validation_fail_empty():
    assert validate_text_field({"text": ""}) is False
