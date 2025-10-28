from app.auth.jwt_utils import create_access_token, verify_token

def test_jwt_auth_flow():
    token = create_access_token({"sub": "niall"})
    payload = verify_token(token)
    assert payload["sub"] == "niall"
