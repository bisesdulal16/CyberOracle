"""
Authentication Router
---------------------
Provides a login endpoint that issues JWT access tokens
and an API key generation endpoint for machine-to-machine access.

Passwords are stored as bcrypt hashes and verified securely.
(OWASP API2: Broken Authentication)

Default dev credentials (override via .env):
    ADMIN_USERNAME        = admin
    ADMIN_PASSWORD_HASH   = <bcrypt hash>
    DEV_USERNAME          = developer
    DEV_PASSWORD_HASH     = <bcrypt hash>
    AUDITOR_USERNAME      = auditor
    AUDITOR_PASSWORD_HASH = <bcrypt hash>
"""

import os

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from app.auth.jwt_utils import create_access_token
from app.auth.rbac import require_roles

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Password hashing context (bcrypt)
# OWASP ASVS V2.4 — passwords must be stored using an adaptive hashing algo
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# Pre-hashed bcrypt defaults for dev credentials
# Generated with: ctx.hash("changeme_X")
# ---------------------------------------------------------------------------
DEFAULT_ADMIN_HASH = "$2b$12$Lzeyj6XunsL3qsbnisC/y.doIuFbqQ9QGQFR9S9M4EMI58ieA9cG6"
DEFAULT_DEV_HASH = "$2b$12$8siDeAW/GlCV8tJs5JVGuO0I5k2HF5IeDyUos75xpk1ePLs7Jye7a"
DEFAULT_AUDITOR_HASH = "$2b$12$e7hBIjGlgnc3kJFjZMzMY.vuZbHCPPySgPKQQ1otXZOTd.3EHMG9S"


class LoginRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_\-\.]+$",
        description="Alphanumeric username. No special characters.",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Password — transmitted over TLS, verified via bcrypt.",
    )


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


def _build_user_store() -> dict:
    """
    Build a username → (hashed_password, role) mapping.
    Reads bcrypt hashes from environment variables.
    Falls back to pre-hashed development defaults.
    """
    return {
        os.getenv("ADMIN_USERNAME", "admin"): (
            os.getenv("ADMIN_PASSWORD_HASH", DEFAULT_ADMIN_HASH),
            "admin",
        ),
        os.getenv("DEV_USERNAME", "developer"): (
            os.getenv("DEV_PASSWORD_HASH", DEFAULT_DEV_HASH),
            "developer",
        ),
        os.getenv("AUDITOR_USERNAME", "auditor"): (
            os.getenv("AUDITOR_PASSWORD_HASH", DEFAULT_AUDITOR_HASH),
            "auditor",
        ),
    }


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """
    Validate credentials and return a signed JWT access token.

    Uses bcrypt verification to prevent timing attacks and
    protect stored credentials.
    OWASP API2: Broken Authentication — never compare passwords in plaintext.
    """
    users = _build_user_store()
    entry = users.get(body.username)

    # Always run bcrypt verify even if user not found
    # Prevents user enumeration via timing differences (OWASP API2)
    dummy_hash = DEFAULT_DEV_HASH
    stored_hash = entry[0] if entry else dummy_hash
    password_valid = pwd_context.verify(body.password, stored_hash)

    if not entry or not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    _, role = entry
    token = create_access_token({"sub": body.username, "role": role})

    return LoginResponse(access_token=token, role=role)


@router.post("/apikey/generate")
async def generate_api_key_endpoint(
    _user: dict = Depends(require_roles("admin")),
):
    """
    Generate a new cryptographically secure API key.
    Only admins can generate API keys.
    OWASP API2: Keys generated with cryptographic randomness via secrets module.
    Store the returned key securely — it will not be shown again.
    """
    from app.auth.api_key_utils import generate_api_key

    key = generate_api_key()
    return {
        "api_key": key,
        "note": "Store this key securely. It will not be shown again.",
    }


@router.get("/me")
async def get_me(_user: dict = Depends(require_roles("admin", "developer", "auditor"))):
    """
    Returns current authenticated user info.
    Used by the frontend to display the role badge and confirm token validity.
    """
    return {
        "username": _user.get("sub"),
        "role": _user.get("role"),
    }
