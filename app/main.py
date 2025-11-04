from fastapi import FastAPI
from app.db.db import Base, engine
from app.routes.logs import router as logs_router
from app.middleware.dlp_filter import DLPFilterMiddleware

from app.routes import logs, secure
from app.middleware.dlp_filter import DLPFilterMiddleware
# Initialize FastAPI application with metadata
app = FastAPI(
    title="CyberOracle Gateway",
    version="1.0.0",
    description="Secure AI gateway ensuring data protection and compliance observability.",
)

# Register custom DLP middleware for sensitive data filtering
app.add_middleware(DLPFilterMiddleware)


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


# Include modular routes for log-related endpoints
app.include_router(logs.router, prefix="/logs", tags=["Logs"])
app.include_router(secure.router, prefix="/secure", tags=["Security"])
