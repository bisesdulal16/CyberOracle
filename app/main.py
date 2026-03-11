from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Database models and async engine
from app.db.db import Base, engine

# Security middleware
from app.middleware.dlp_filter import DLPFilterMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware

# API routers
from app.routes.ai import router as ai_router
from app.routes.dlp import router as dlp_router
from app.routes.logs import router as logs_router
from app.routes.metrics import router as metrics_router

# Global secure exception handler
from app.utils.exception_handler import secure_exception_handler


# ------------------------------------------------
# Application Lifespan
# ------------------------------------------------
# Runs on application startup and shutdown.
# Used here to ensure database tables are created
# before the API begins serving requests.
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # Create database tables if they do not exist
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Optional shutdown logic
    # Example:
    # await engine.dispose()


# ------------------------------------------------
# FastAPI Application Initialization
# ------------------------------------------------
app = FastAPI(
    title="CyberOracle Gateway",
    version="1.0.0",
    description="Secure AI gateway ensuring data protection and compliance observability.",
    lifespan=lifespan,
)


# ------------------------------------------------
# CORS Configuration
# ------------------------------------------------
# Restricts browser access to local development origins only.
# Prevents unauthorized websites from making requests to the API.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------
# Security Middleware Stack
# ------------------------------------------------
# Order matters:
# 1. DLP filter scans requests for sensitive data
# 2. Rate limiter protects API from abuse
app.add_middleware(DLPFilterMiddleware)
app.add_middleware(RateLimitMiddleware)


# ------------------------------------------------
# Global Exception Handler
# ------------------------------------------------
# Ensures sensitive internal errors are not exposed
# to API clients while still being logged securely.
app.add_exception_handler(Exception, secure_exception_handler)


# ------------------------------------------------
# Health Check Endpoint
# ------------------------------------------------
# Used by:
# - monitoring systems
# - container orchestration
# - uptime checks
@app.get("/health")
async def health():
    return {"status": "OK", "service": "CyberOracle API"}


# ------------------------------------------------
# Router Registration
# ------------------------------------------------

# AI Gateway endpoints
# Example: /ai/query
app.include_router(ai_router, prefix="/ai", tags=["AI Gateway"])

# Log storage and retrieval
# Example: /logs
app.include_router(logs_router, prefix="/logs", tags=["Logs"])

# DLP scanning endpoints
# Example: /api/dlp/scan
app.include_router(dlp_router, prefix="/api", tags=["DLP"])

# System metrics and observability endpoints
# Example: /metrics
app.include_router(metrics_router)