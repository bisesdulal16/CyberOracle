from app.auth.jwt_utils import create_access_token, verify_token


def test_jwt_creation_and_verification():
    payload = {"user": "niall"}
    token = create_access_token(payload)
    decoded = verify_token(token)
    assert decoded["user"] == "niall"


def test_jwt_invalid_token():
    fake = "abc.def.ghi"
    try:
        verify_token(fake)
        assert False
    except Exception:
        assert True
