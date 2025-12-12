from fastapi.responses import JSONResponse
from fastapi import Request
import logging

logger = logging.getLogger("cyberoracle")


async def secure_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=500, content={"detail": "Internal server error. Reference logged."}
    )
