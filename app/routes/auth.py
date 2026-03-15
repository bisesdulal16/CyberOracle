"""
Authentication Router
---------------------
Provides a login endpoint that issues JWT access tokens.

Credentials are read from environment variables so the client can
configure accounts without code changes.

Default dev credentials (override via .env):
    ADMIN_USERNAME   = admin      ADMIN_PASSWORD   = changeme_admin
    DEV_USERNAME     = developer  DEV_PASSWORD     = changeme_dev
    AUDITOR_USERNAME = auditor    AUDITOR_PASSWORD = changeme_auditor

Security note
-------------
This is a simple credential-store suitable for Capstone I.
Production deployments should replace this with a proper identity
provider (OAuth2 / OIDC).
"""

import os

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.auth.jwt_utils import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


# ---------------------------------------------------------------------------
# Credential store (env-driven)
# ---------------------------------------------------------------------------


def _build_user_store() -> dict:
    """
    Build a username → (password, role) mapping from environment variables.
    Falls back to development defaults when env vars are absent.
    """
    return {
        os.getenv("ADMIN_USERNAME", "admin"): (
            os.getenv("ADMIN_PASSWORD", "changeme_admin"),
            "admin",
        ),
        os.getenv("DEV_USERNAME", "developer"): (
            os.getenv("DEV_PASSWORD", "changeme_dev"),
            "developer",
        ),
        os.getenv("AUDITOR_USERNAME", "auditor"): (
            os.getenv("AUDITOR_PASSWORD", "changeme_auditor"),
            "auditor",
        ),
    }


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """
    Validate credentials and return a signed JWT access token.

    The token payload includes {"sub": username, "role": role}.
    The frontend should store the token and attach it to subsequent
    requests as:  Authorization: Bearer <token>
    """
    users = _build_user_store()

    entry = users.get(body.username)
    if entry is None or entry[0] != body.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    password, role = entry
    token = create_access_token({"sub": body.username, "role": role})

    return LoginResponse(access_token=token, role=role)
