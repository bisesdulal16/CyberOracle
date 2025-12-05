from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging
import re

logger = logging.getLogger("cyberoracle")


def mask_sensitive_value(value: str):
    """Mask passwords, SSNs, and other sensitive inputs."""
    if not isinstance(value, str):
        return value

    # Mask password-like fields fully
    if len(value) < 50:  # avoid masking normal long text
        # If it's clearly a password attempt
        if re.search(r"[A-Za-z0-9@#$%^&+=!]", value):
            return "***MASKED***"

    # Mask SSN patterns
    value = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "***SSN_MASKED***", value)

    return value


async def secure_exception_handler(request: Request, exc: Exception):

    # ===============================================
    # 1️⃣ Handle Pydantic validation errors
    # ===============================================
    if isinstance(exc, (ValidationError, RequestValidationError)):
        errors = exc.errors()

        # Mask sensitive data in errors
        for err in errors:
            if "input" in err:
                err["input"] = mask_sensitive_value(err["input"])

        # Log sanitized errors
        logger.error("Pydantic Validation Error (sanitized):")
        logger.error(errors)

        # Return clean formatted errors for UI (no "object Object")
        formatted_errors = [
            f"{err['loc'][-1].capitalize()}: {err['msg']}" for err in errors
        ]

        return JSONResponse(
            status_code=422,
            content={"detail": "Input validation failed.", "errors": formatted_errors},
        )

    # ===============================================
    # 2️⃣ Pass through HTTPExceptions normally
    # ===============================================
    from fastapi.exceptions import HTTPException

    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    # ===============================================
    # 3️⃣ Unexpected server errors → masked logs
    # ===============================================
    logger.error(f"Unhandled exception: {mask_sensitive_value(str(exc))}")

    return JSONResponse(
        status_code=500, content={"detail": "Internal server error. Reference logged."}
    )
