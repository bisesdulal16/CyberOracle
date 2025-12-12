from pydantic import BaseModel, constr
from typing import Optional


class LogEntry(BaseModel):
    action: constr(strip_whitespace=True)
    status: Optional[str] = "OK"
    message: Optional[str] = None


class LogIngest(BaseModel):
    message: str
