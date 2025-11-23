"""
Rate Limiting Middleware
------------------------
Provides a simple sliding-window rate limiter for API protection.
Week 2 Deliverable — Niall Chiweshe
"""

import os
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


def is_test_mode() -> bool:
    """Check test mode dynamically so pytest can enable it at runtime."""
    return os.getenv("PYTEST") == "1"


# Behavior: real server = 1000/sec, tests = 5/min
if is_test_mode():
    RATE_LIMIT = 5
    TIME_WINDOW = 60
else:
    RATE_LIMIT = 1000
    TIME_WINDOW = 1

# In-memory request tracker
requests_log = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Disable rate limiting during pytest unless explicitly enabled
        if is_test_mode() and not os.getenv("DISABLE_RATE_LIMIT_TEST"):
            return await call_next(request)

        client_ip = request.client.host
        now = time.time()

        # Ensure this IP has a history list
        history = requests_log.setdefault(client_ip, [])

        # Remove timestamps older than window
        history = [t for t in history if now - t < TIME_WINDOW]
        requests_log[client_ip] = history

        # Enforce limit
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

        # Log timestamp
        history.append(now)
        requests_log[client_ip] = history

        return await call_next(request)


# -------------------------------------------------------------
# 🧹 Pytest helper: reset state before each test
# -------------------------------------------------------------
def reset_rate_limit_state():
    """Reset the in-memory rate limiter history for pytest."""
    global requests_log
    requests_log = {}
