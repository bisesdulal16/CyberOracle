"""
DLP (Data Loss Prevention) Middleware
-------------------------------------
Purpose:
Intercepts incoming POST, PUT, and PATCH requests and scans them for
sensitive data such as SSNs, credit card numbers, emails, or API keys.
If detected, the values are redacted ("***") before the data reaches the
main application or database layer.

This ensures sensitive information is never logged, stored, or leaked.
"""

import re
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Dictionary of regex patterns that match sensitive data formats
SENSITIVE_PATTERNS = {
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": (
        r"\b(?:\d[ -]*?){13,16}\b"
    ),  # matches 13–16 digit credit card numbers with/without spaces or dashes
    "email": (
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    ),  # matches standard email address formats
    "api_key": (
        r"\b[A-Za-z0-9]{32,}\b"
    ),  # matches long alphanumeric strings often used as API keys or tokens
}


class DLPFilterMiddleware(BaseHTTPMiddleware):
    """
    Custom FastAPI middleware that scans and redacts sensitive data from
    incoming request bodies before they are processed by router handlers.
    """

    async def dispatch(self, request: Request, call_next):
        # Target only data-carrying methods
        if request.method in {"POST", "PUT", "PATCH"}:
            try:
                body = await request.json()
            except Exception:
                body = {}

            redacted = False

            for key, value in body.items():
                if isinstance(value, str):
                    for _, pattern in SENSITIVE_PATTERNS.items():
                        if re.search(pattern, value):
                            body[key] = re.sub(pattern, "***", value)
                            redacted = True

            # Replace the request body with the sanitized version if any sensitive data was found
            if redacted:
                request._body = json.dumps(body).encode("utf-8")

        response = await call_next(request)
        return response
