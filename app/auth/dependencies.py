from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from app.auth.jwt_utils import verify_token
from app.auth.api_key_utils import validate_api_key

API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME)

# Replace this with your actual stored API key
STORED_API_KEY = "my_secret_api_key_123"


async def api_key_required(api_key: str = Security(api_key_header)):
    if not validate_api_key(api_key, STORED_API_KEY):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key


async def get_current_user(token: str):
    """
    token: raw JWT string from Authorization header
    """
    try:
        payload = verify_token(token)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid JWT token")


def require_role(role: str):
    async def role_checker(user=Depends(get_current_user)):
        if user.get("role") != role:
            raise HTTPException(status_code=403, detail="Insufficient privileges")
        return user

    return role_checker
