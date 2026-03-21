import os
from datetime import datetime, timedelta, timezone
from jose import jwt

ALGORITHM = "HS256"

def create_access_token(subject: str, expires_minutes: int = 60) -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET is not set")

    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)