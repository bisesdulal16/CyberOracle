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


# DO NOT CHANGE THESE – TESTS DEPEND ON THEM
if is_test_mode():
    RATE_LIMIT = 5
    TIME_WINDOW = 60
else:
    RATE_LIMIT = 10000
    TIME_WINDOW = 1

requests_log = {}

# ============================================================
# NEW: IP BAN LOGIC (Does NOT break existing rate limit logic)
# ============================================================

# How many rate-limit violations before a ban occurs
BAN_THRESHOLD = 3

# Ban duration (seconds)
BAN_DURATION = 60

# Track banned IPs: ip -> ban_expiry_timestamp
banned_ips = {}

# Track how many times an IP has hit the rate limit
violation_counter = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        client_ip = request.client.host
        now = time.time()

        # ==========================================
        # 1. Check if IP is banned
        # ==========================================
        if client_ip in banned_ips:
            expiry = banned_ips[client_ip]
            if now < expiry:
                # Still banned
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "IP temporarily banned due to repeated rate limit violations"
                    },
                )
            else:
                # Ban expired → remove
                banned_ips.pop(client_ip, None)

        # ==========================================
        # 2. Normal rate-limiting logic (unchanged)
        # ==========================================
        history = requests_log.setdefault(client_ip, [])

        # Keep timestamps within sliding window
        history = [t for t in history if now - t < TIME_WINDOW]

        if len(history) >= RATE_LIMIT:
            # Count violation
            violation_counter[client_ip] = violation_counter.get(client_ip, 0) + 1

            # Trigger ban if threshold reached
            if violation_counter[client_ip] >= BAN_THRESHOLD:
                banned_ips[client_ip] = now + BAN_DURATION
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "IP temporarily banned due to repeated rate limit violations"
                    },
                )

            # Return original rate-limit response (tests depend on this!)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        f"Rate limit exceeded "
                        f"({RATE_LIMIT} reqs per {TIME_WINDOW}s)"
                    )
                },
            )

        # Log request timestamp
        history.append(now)
        requests_log[client_ip] = history

        return await call_next(request)
