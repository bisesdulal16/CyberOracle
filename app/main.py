from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.db import Base, engine
from app.routes.logs import router as logs_router
from app.routes.dlp import router as dlp_router  # import DLP routes
from app.middleware.dlp_filter import DLPFilterMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.utils.exception_handler import secure_exception_handler
from app.routes.metrics import router as metrics_router
from app.routes.ai import router as ai_router

# Initialize FastAPI application with metadata
app = FastAPI(
    title="CyberOracle Gateway",
    version="1.0.0",
    description="Secure AI gateway ensuring data protection and compliance observability.",
)

# UI → backend calls)
app.add_middleware(
    CORSMiddleware,
    # Allow any localhost/127.0.0.1 port during development
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom DLP middleware for sensitive data filtering
app.add_middleware(DLPFilterMiddleware)

# Register cutstom Rate-Limiting middleware
app.add_middleware(RateLimitMiddleware)

# Register custom Exception Handler middleware
app.add_exception_handler(Exception, secure_exception_handler)


# Health check endpoint to verify uptime and API status
@app.get("/health")
async def health():
    """
    Returns basic service health information.
    Used for monitoring, CI/CD checks, and Kubernetes readiness probes.
    """
    return {"status": "OK", "service": "CyberOracle API"}


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Include modular routes
app.include_router(logs_router, prefix="/logs", tags=["Logs"])
app.include_router(dlp_router, prefix="/api", tags=["DLP"])

# include metrics router for dashboard APIs
app.include_router(metrics_router)  # routes already have prefix="/api"

# AI gateway endpoint /ai/query
app.include_router(ai_router, tags=["AI"])
