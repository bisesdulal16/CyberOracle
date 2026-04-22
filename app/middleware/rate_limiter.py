"""
Rate Limiting Middleware
------------------------
Implements per-IP, per-role sliding window rate limiting.

Roles and limits are driven by policy.yaml:
(OWASP API Security Top 10 – API4: Unrestricted Resource Consumption).
Falls back to a conservative default for unauthenticated requests.

Monitoring/health endpoints are exempt from rate limiting to prevent
dashboard polling from consuming the user's request budget.
"""

import os
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware

# ---------------------------------------------------------------------------
# Endpoints exempt from rate limiting
# These are polled automatically by the dashboard and should not count
# toward a user's request budget.
# ---------------------------------------------------------------------------
EXEMPT_PATHS = {
    "/health",
    "/api/metrics/summary",
    "/api/metrics/timeline",
    "/api/alerts/recent",
    "/api/compliance/status",
    "/logs/list",
}

# Role-based limits (requests per window) — mirrors policy.yaml
ROLE_LIMITS: dict[str, int] = {
    "admin": 1000,
    "developer": 100,
    "auditor": 50,
}

# Unauthenticated / unknown role gets the most restrictive limit
DEFAULT_LIMIT = 30

# Window size in seconds
PROD_TIME_WINDOW = 60

# Tighter limits in test mode so tests run quickly
TEST_RATE_LIMIT = 5
TEST_TIME_WINDOW = 60

# In-memory store: key → list of request timestamps
requests_log: dict[str, list[float]] = {}

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_only_secret_change_in_prod")
ALGORITHM = "HS256"


def _get_role_from_request(request: Request) -> str | None:
    """Extract role from JWT Bearer token if present. Returns None if absent or invalid."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("role")
    except JWTError:
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        # ------------------------------------------------------------------
        # Exempt dashboard polling and health check endpoints
        # ------------------------------------------------------------------
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        test_mode = os.getenv("PYTEST") == "1"

        # Allow tests to opt OUT of rate limiting entirely
        if test_mode and os.getenv("DISABLE_RATE_LIMIT_TEST") == "1":
            return await call_next(request)

        # Resolve limits for this request
        if test_mode:
            rate_limit = TEST_RATE_LIMIT
            time_window = TEST_TIME_WINDOW
        else:
            role = _get_role_from_request(request)
            rate_limit = ROLE_LIMITS.get(role, DEFAULT_LIMIT) if role else DEFAULT_LIMIT
            time_window = PROD_TIME_WINDOW

        # Build a tracking key: IP + role so roles don't share buckets
        role_tag = _get_role_from_request(request) or "anon"
        client_ip = request.client.host if request.client else "unknown"
        bucket_key = f"{client_ip}:{role_tag}"

        now = time.time()
        history = requests_log.setdefault(bucket_key, [])
        history = [t for t in history if now - t < time_window]

        if len(history) >= rate_limit:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        f"Rate limit exceeded "
                        f"({rate_limit} requests per {time_window}s)"
                    )
                },
            )

        history.append(now)
        requests_log[bucket_key] = history

        return await call_next(request)
