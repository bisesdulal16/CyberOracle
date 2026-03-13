"""
Rate Limiting Middleware
------------------------
Provides a simple sliding-window rate limiter for API protection.
"""

import os
import sys
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

RATE_LIMIT = 5
TIME_WINDOW = 60

requests_log = {}


def is_test_mode() -> bool:
    return os.getenv("PYTEST") == "1" or "pytest" in sys.modules


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Bypass rate limiting for tests unless a test explicitly enables it
        if is_test_mode() and os.getenv("ENABLE_RATE_LIMIT_TEST") != "1":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        history = requests_log.setdefault(client_ip, [])
        history = [t for t in history if now - t < TIME_WINDOW]

        if len(history) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        f"Rate limit exceeded "
                        f"({RATE_LIMIT} reqs per {TIME_WINDOW}s)"
                    )
                },
            )

        history.append(now)
        requests_log[client_ip] = history

        return await call_next(request)
