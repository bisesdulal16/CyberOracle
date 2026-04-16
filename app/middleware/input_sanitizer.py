import re
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse


# Basic injection patterns to block globally
FORBIDDEN_PATTERNS = [
    r";",  # SQL termination
    r"--",  # SQL comment
    r"\/\*",  # SQL block comment
    r"\*\/",
    r"<script>",  # XSS
    r"</script>",
    r"SELECT\s",  # SQL keyword
    r"DROP\s",
    r"INSERT\s",
    r"DELETE\s",
    r"UPDATE\s",
]


def contains_malicious_pattern(value: str) -> bool:
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    return False


class InputSanitizerMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.json()
            except Exception:
                return await call_next(request)

            # Recursively inspect JSON payload
            if isinstance(body, dict):
                for key, value in body.items():
                    if isinstance(value, str):
                        if contains_malicious_pattern(value):
                            return JSONResponse(
                                status_code=400,
                                content={
                                    "detail": "Input contains unsafe or malicious patterns."
                                },
                            )

        return await call_next(request)
