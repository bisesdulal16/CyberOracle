from fastapi import FastAPI
from app.db.db import Base, engine
from app.routes.logs import router as logs_router
from app.routes.dlp import router as dlp_router
from app.middleware.dlp_filter import DLPFilterMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.utils.exception_handler import secure_exception_handler
from app.routes.auth_routes import router as auth_router

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# For validation error interception
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError


# ---------------------------------------------------------
# Initialize FastAPI
# ---------------------------------------------------------
app = FastAPI(
    title="CyberOracle Gateway",
    version="1.0.0",
    description="Secure AI gateway ensuring data protection and compliance observability.",
)

# ---------------------------------------------------------
# Middleware Registration
# ---------------------------------------------------------
app.add_middleware(DLPFilterMiddleware)
app.add_middleware(RateLimitMiddleware)

# Custom exception handlers
app.add_exception_handler(Exception, secure_exception_handler)
app.add_exception_handler(RequestValidationError, secure_exception_handler)
app.add_exception_handler(ValidationError, secure_exception_handler)


# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "OK", "service": "CyberOracle API"}


# ---------------------------------------------------------
# Startup DB Initialization
# ---------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ---------------------------------------------------------
# Static Frontend UI
# ---------------------------------------------------------
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/login")
async def login_page():
    return FileResponse("app/static/login.html")


@app.get("/signup")
async def signup_page():
    return FileResponse("app/static/signup.html")


@app.get("/dashboard")
async def dashboard_router():
    return FileResponse("app/static/dashboard_router.html")


@app.get("/dashboard_admin")
async def admin_dashboard():
    return FileResponse("app/static/dashboard_admin.html")


@app.get("/dashboard_user")
async def user_dashboard():
    return FileResponse("app/static/dashboard_user.html")


# ---------------------------------------------------------
# API Routers (Backend Functionality)
# ---------------------------------------------------------
app.include_router(logs_router, prefix="/logs", tags=["Logs"])
app.include_router(dlp_router, prefix="/api", tags=["DLP"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(auth_router)  # (duplicate safe, needed for some imports)
