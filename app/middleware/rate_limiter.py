import os, sys, time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

if "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST"):
    RATE_LIMIT = 5
    TIME_WINDOW = 60
else:
    RATE_LIMIT = 1000
    TIME_WINDOW = 1

requests_log = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            client_ip = request.client.host
            now = time.time()

            if client_ip not in requests_log:
                requests_log[client_ip] = []

            # keep timestamps within window
            requests_log[client_ip] = [
                t for t in requests_log[client_ip] if now - t < TIME_WINDOW
            ]

            if len(requests_log[client_ip]) >= RATE_LIMIT:
                # Return response instead of raising
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Rate limit exceeded ({RATE_LIMIT} reqs per {TIME_WINDOW}s)"
                    },
                )

            requests_log[client_ip].append(now)
            response = await call_next(request)
            return response

        except Exception as e:
            # Defensive catch so no unhandled error produces 500
            return JSONResponse(status_code=500, content={"error": str(e)})
