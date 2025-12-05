# app/schemas/log_schema.py
from pydantic import BaseModel, constr, validator
from typing import Optional
import re


class LogEntry(BaseModel):
    action: constr(strip_whitespace=True)
    status: Optional[str] = "OK"
    message: Optional[str] = None

    @validator("action", "message", pre=True, always=True)
    def sanitize_text(cls, v):
        if v is None:
            return v
        # Remove SQL/HTML special characters
        return re.sub(r"[<>;'\"--]", "", v)


class LogIngest(BaseModel):
    message: constr(strip_whitespace=True, min_length=1, max_length=500)

    @validator("message", pre=True, always=True)
    def sanitize_message(cls, v):
        # Remove potentially dangerous characters
        return re.sub(r"[<>;'\"--]", "", v)
