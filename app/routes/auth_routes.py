# app/routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, constr, validator
import re

from app.auth.user_store import authenticate_user
from app.auth.jwt_utils import create_access_token, verify_token

router = APIRouter(prefix="/auth")

bearer_scheme = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        payload = verify_token(credentials.credentials)
        return payload
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ================================
# Input validation model
# ================================
class LoginRequest(BaseModel):
    username: constr(strip_whitespace=True, min_length=3, max_length=50)
    password: constr(strip_whitespace=True, min_length=8, max_length=128)

    @validator('username')
    def username_safe(cls, v):
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError('Username contains invalid characters')
        return v

# Login endpoint
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Validate input manually
    login_data = LoginRequest(username=form_data.username, password=form_data.password)

    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    access_token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}


# Protected route
@router.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello {current_user['sub']}! You have access.", "role": current_user["role"]}
