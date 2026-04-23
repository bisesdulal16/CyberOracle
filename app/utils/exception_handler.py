"""
Secure Global Exception Handler
---------------------------------
Catches all unhandled exceptions at the application level and returns
a safe generic response without leaking internal details.

OWASP API Security Top 10:
- API7: Security Misconfiguration — never expose stack traces or
  internal error messages to API clients.
- Detailed errors are logged server-side for debugging only.
"""

import logging
import traceback

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("cyberoracle")


async def secure_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler — returns generic message, logs full detail.

    The client receives only:
        {"detail": "Internal server error. Reference logged."}

    The server logs:
        - Exception type and message
        - Request path and method
        - Full traceback (server-side only)

    This prevents stack traces, connection strings, and internal
    paths from being exposed to API clients.
    """
    # Log full detail server-side for debugging
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path} — "
        f"{type(exc).__name__}: {exc}"
    )

    # Log traceback at DEBUG level so it's available when needed
    logger.debug(traceback.format_exc())

    # Return generic message — never expose exc details to client
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Reference logged."},
    )