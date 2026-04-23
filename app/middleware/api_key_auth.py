"""
API Key Authentication Dependency
----------------------------------
Allows routes to accept an X-API-Key header as an alternative
to JWT Bearer tokens. Used for machine-to-machine access.

OWASP API2: Broken Authentication
- Keys are compared using secrets.compare_digest (timing-safe)
- Keys are read from environment variables, never hardcoded
- Returns a synthetic JWT-compatible user payload on success
"""

import os
from fastapi import Header, HTTPException, status
from app.auth.api_key_utils import validate_api_key


async def verify_api_key(x_api_key: str = Header(...)):
    """
    FastAPI dependency that validates the X-API-Key header.

    Usage:
        @router.post("/endpoint")
        async def endpoint(_=Depends(verify_api_key)):
            ...

    The SYSTEM_API_KEY environment variable must be set.
    Generate a key via POST /auth/apikey/generate (admin only).
    """
    stored_key = os.getenv("SYSTEM_API_KEY", "")

    if not stored_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key authentication not configured on this server.",
        )

    if not validate_api_key(x_api_key, stored_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    # Return synthetic user payload matching JWT structure
    # so downstream RBAC logic works identically
    return {"sub": "api_client", "role": "developer"}
