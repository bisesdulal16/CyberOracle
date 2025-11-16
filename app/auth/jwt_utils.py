"""
JWT Utility Module
------------------
Handles creation and verification of JSON Web Tokens.
Built following OWASP recommendations for signing,
expiration enforcement, and algorithm safety.
"""

from datetime import datetime, timedelta
from jose import jwt, JWTError

SECRET_KEY = "dev_only_secret_change_in_prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict) -> str:
    """
    Create a JWT access token embedding a user payload.
    Includes expiration claims and secure signing.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """
    Verify a JWT access token and return its decoded payload.
    Raises JWTError for invalid or expired tokens.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise ValueError("Invalid or expired JWT token")
