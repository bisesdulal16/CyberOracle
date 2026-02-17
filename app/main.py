from fastapi import FastAPI
from app.db.db import Base, engine
from app.routes.logs import router as logs_router
from app.routes.dlp import router as dlp_router  # import DLP routes
from app.middleware.dlp_filter import DLPFilterMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.utils.exception_handler import secure_exception_handler
from app.routes.ai import router as ai_router
from contextlib import asynccontextmanager

# Initialize FastAPI application with metadata
app = FastAPI(
    title="CyberOracle Gateway",
    version="1.0.0",
    description="Secure AI gateway ensuring data protection and compliance observability.",
)

# Register custom DLP middleware for sensitive data filtering
app.add_middleware(DLPFilterMiddleware)

# Register cutstom Rate-Limiting middleware
app.add_middleware(RateLimitMiddleware)

# Register custom Exception Handler middleware
app.add_exception_handler(Exception, secure_exception_handler)

app.include_router(ai_router, prefix="/ai", tags=["AI Gateway"])


# Health check endpoint to verify uptime and API status
@app.get("/health")
async def health():
    """
    Returns basic service health information.
    Used for monitoring, CI/CD checks, and Kubernetes readiness probes.
    """
    return {"status": "OK", "service": "CyberOracle API"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # shutdown (optional): close pools if you want
    # await engine.dispose()


# Include modular routes
app.include_router(logs_router, prefix="/logs", tags=["Logs"])
app.include_router(dlp_router, prefix="/api", tags=["DLP"])
