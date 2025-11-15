import pytest
from app.utils.validation import sanitize_input, validate_email
from fastapi import HTTPException


def test_sanitize_input_removes_symbols():
    text = "<script>;DROP TABLE;"
    clean = sanitize_input(text)
    assert "<" not in clean and ";" not in clean


def test_validate_email_success():
    assert validate_email("user@example.com") == "user@example.com"


def test_validate_email_fail():
    with pytest.raises(HTTPException):
        validate_email("bad_email")
