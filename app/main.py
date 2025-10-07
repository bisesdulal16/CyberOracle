from fastapi import FastAPI, Depends
from app.middleware.dlp_middleware import DLPProtectionMiddleware
from auth.rbac import get_current_user, RoleChecker

app = FastAPI(title="CyberOracle API")

# Register middleware
app.add_middleware(DLPProtectionMiddleware)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/admin")
def admin_route(current_user: dict = Depends(get_current_user)):
    RoleChecker(["admin"])(current_user)
    return {"message": "Welcome Admin!"}
