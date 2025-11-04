"""
Input Validation Utilities
--------------------------
Sanitize and validate inbound data before processing.
"""

import re
from fastapi import HTTPException

def sanitize_input(value: str) -> str:
    """Remove suspicious characters like < > ;"""
    return re.sub(r'[<>;]', '', value)

def validate_email(email: str):
    """Simple email validator using regex."""
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    return email
