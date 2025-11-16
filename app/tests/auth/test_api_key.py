from app.auth.api_key_utils import generate_api_key, validate_api_key


def test_generate_api_key_length():
    key = generate_api_key()
    assert len(key) == 64  # 32 bytes hex → 64 chars


def test_validate_api_key_success():
    key = generate_api_key()
    assert validate_api_key(key, key) is True


def test_validate_api_key_failure():
    key1 = generate_api_key()
    key2 = generate_api_key()
    assert validate_api_key(key1, key2) is False
