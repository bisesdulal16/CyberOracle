"""
Log Schemas
-----------
Pydantic models for log ingestion validation.
Input sanitization applied to all string fields.
OWASP API3: Broken Object Property Level Authorization
"""

from pydantic import BaseModel, Field, constr
from typing import Optional


class LogEntry(BaseModel):
    action: constr(strip_whitespace=True, min_length=1, max_length=200)
    status: Optional[constr(strip_whitespace=True, max_length=50)] = "OK"
    message: Optional[constr(strip_whitespace=True, max_length=2000)] = None


class LogIngest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Log message — must be pre-masked before submission.",
    )
