from fastapi import APIRouter, Depends, HTTPException, Header
from app.auth.jwt_utils import verify_token

router = APIRouter()

async def get_current_user(Authorization: str = Header(None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")

    token = Authorization.split(" ")[1]
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload

@router.get("/hello")
async def hello_secure(user = Depends(get_current_user)):
    return {"message": f"Hello {user['sub']}!"}
