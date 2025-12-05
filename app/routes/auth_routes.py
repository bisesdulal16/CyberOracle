# app/routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from pydantic import BaseModel, constr, validator
import re

from app.auth.user_store import authenticate_user, create_user
from app.auth.jwt_utils import create_access_token, verify_token

router = APIRouter(prefix="/auth")

bearer_scheme = HTTPBearer()


# -------------------------------------------------------------------
# Token Verification
# -------------------------------------------------------------------
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    try:
        payload = verify_token(credentials.credentials)
        return payload
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )


# -------------------------------------------------------------------
# OWASP-Compliant Input Models
# -------------------------------------------------------------------
class SignupRequest(BaseModel):
    username: constr(strip_whitespace=True, min_length=3, max_length=50)
    password: constr(strip_whitespace=True, min_length=8, max_length=128)

    @validator("username")
    def username_safe(cls, v):
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError(
                "Username must only contain letters, numbers, underscores, periods, or hyphens."
            )
        return v

    @validator("password")
    def strong_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must include at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must include at least one lowercase letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must include at least one number.")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("Password must include at least one special character.")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


# -------------------------------------------------------------------
# SIGNUP ENDPOINT
# -------------------------------------------------------------------
@router.post("/signup")
async def signup(payload: SignupRequest):
    """Create a new user with OWASP password validation."""
    try:
        validated = payload
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid signup input. Review OWASP credential guidelines.",
        )

    # Create user (always standard user role)
    create_user(username=validated.username, password=validated.password)

    return {"message": "Account created successfully. You may now log in."}


# -------------------------------------------------------------------
# LOGIN ENDPOINT
# -------------------------------------------------------------------
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        validated = LoginRequest(
            username=form_data.username,
            password=form_data.password,
        )
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="Invalid login format. Review OWASP credential guidelines.",
        )

    user = authenticate_user(validated.username, validated.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication failed. Verify username and password.",
        )

    token = create_access_token({"sub": user["username"], "role": user["role"]})

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
    }


# -------------------------------------------------------------------
# TEST PROTECTED ROUTE
# -------------------------------------------------------------------
@router.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {
        "message": f"Hello {current_user['sub']}! Access granted.",
        "role": current_user["role"],
    }
