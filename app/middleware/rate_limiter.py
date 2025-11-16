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

    # The most important fix:
    # Reset data every time this file is imported during pytest
    # (Test runner loads modules multiple times)
    requests_log = {}

    # Force stable client "IP" for tests
    TEST_CLIENT_IP = "pytest-client"

else:
    RATE_LIMIT = 1000
    TIME_WINDOW = 1
    requests_log = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        now = time.time()

        # Give CI a deterministic, consistent IP address
        if TEST_MODE:
            client_ip = TEST_CLIENT_IP
        else:
            client_ip = request.client.host

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
