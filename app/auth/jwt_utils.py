"""
JWT Utility Module
------------------
Handles creation and verification of JSON Web Tokens.
Built following OWASP recommendations for signing,
expiration enforcement, and algorithm safety.
"""

import os
from datetime import datetime, timedelta

from jose import jwt, JWTError

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_only_secret_change_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict) -> str:
    """
    Create a JWT access token embedding a user payload.
    Includes expiration claims and secure signing.
    """
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # CHANGED: explicitly add expiration AND issued-at timestamps
    # Issued-at helps with auditing and token validation in distributed systems
    to_encode.update(
        {"exp": expire, "iat": datetime.utcnow()}  # ADDED: issued-at timestamp
    )

    # IMPORTANT:
    # The incoming `data` dictionary MUST contain:
    #   {
    #       "sub": username,
    #       "role": user_role
    #   }
    #
    # RBAC depends on the "role" claim being present in the token payload.

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """
    Verify a JWT access token and return its decoded payload.
    Raises JWTError for invalid or expired tokens.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # ADDED: additional defensive validation to ensure required RBAC fields exist
        if "sub" not in payload:
            raise ValueError("JWT missing subject claim")

        if "role" not in payload:
            raise ValueError("JWT missing role claim required for RBAC")

        return payload

    except JWTError:
        raise ValueError("Invalid or expired JWT token")
