import os
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Production defaults — overridden dynamically per-request in test mode
PROD_RATE_LIMIT = 1000
PROD_TIME_WINDOW = 1

TEST_RATE_LIMIT = 5
TEST_TIME_WINDOW = 60

requests_log: dict[str, list[float]] = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        test_mode = os.getenv("PYTEST") == "1"

        # Allow tests to opt OUT of rate limiting (e.g. for unrelated endpoint tests)
        if test_mode and os.getenv("DISABLE_RATE_LIMIT_TEST") == "1":
            return await call_next(request)

        # Pick limits dynamically so env vars set after import still apply
        rate_limit = TEST_RATE_LIMIT if test_mode else PROD_RATE_LIMIT
        time_window = TEST_TIME_WINDOW if test_mode else PROD_TIME_WINDOW

        client_ip = request.client.host
        now = time.time()

        history = requests_log.setdefault(client_ip, [])
        history = [t for t in history if now - t < time_window]

        if len(history) >= rate_limit:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        f"Rate limit exceeded "
                        f"({rate_limit} reqs per {time_window}s)"
                    )
                },
            )

        history.append(now)
        requests_log[client_ip] = history

        return await call_next(request)
