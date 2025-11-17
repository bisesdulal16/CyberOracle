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

# Test mode configuration
TEST_MODE = os.getenv("PYTEST") == "1"

if TEST_MODE:
    RATE_LIMIT = 5
    TIME_WINDOW = 60
else:
    RATE_LIMIT = 1000
    TIME_WINDOW = 1

requests_log = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Disable rate limiting during pytest
        if TEST_MODE and not os.getenv("DISABLE_RATE_LIMIT_TEST"):
            return await call_next(request)

        client_ip = request.client.host
        now = time.time()

        history = requests_log.setdefault(client_ip, [])

        # Keep timestamps within window
        history = [t for t in history if now - t < TIME_WINDOW]

        # Too many requests?
        if len(history) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded ({RATE_LIMIT} reqs per {TIME_WINDOW}s)"
                },
            )

        # Log this request
        history.append(now)
        requests_log[client_ip] = history

        return await call_next(request)
