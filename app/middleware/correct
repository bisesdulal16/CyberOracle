"""
Rate Limiting Middleware
------------------------
Prevents brute-force or DDoS-style traffic by tracking
requests per client IP within a fixed time window.
"""

import os
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Enable deterministic behavior for pytest
TEST_MODE = os.getenv("PYTEST") == "1"

if TEST_MODE:
    RATE_LIMIT = 5
    TIME_WINDOW = 60
else:
    RATE_LIMIT = 1000
    TIME_WINDOW = 1

# global in-memory store
requests_log = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

        # Clear log ONCE when test starts, not per request
        if TEST_MODE:
            requests_log.clear()

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()

        if client_ip not in requests_log:
            requests_log[client_ip] = []

        # Keep only recent timestamps
        requests_log[client_ip] = [
            t for t in requests_log[client_ip] if now - t < TIME_WINDOW
        ]

        # Block BEFORE adding new request
        if len(requests_log[client_ip]) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded ({RATE_LIMIT} reqs per {TIME_WINDOW}s)"
                },
            )

        # Log request
        requests_log[client_ip].append(now)

        return await call_next(request)
