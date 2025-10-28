from app.auth.api_key_utils import generate_api_key, validate_api_key

def test_api_key_validation():
    key = generate_api_key("niall")
    assert validate_api_key(key)
    assert not validate_api_key("invalid")
