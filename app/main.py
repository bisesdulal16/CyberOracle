from fastapi import FastAPI
from app.routes import logs

app = FastAPI(
    title="CyberOracle Gateway",
    version="1.0.0",
    description="Secure AI gateway ensuring data protection and compliance observability."
)

@app.get("/health")
async def health():
    return {"status": "OK", "service": "CyberOracle API"}

app.include_router(logs.router, prefix="/logs", tags=["Logs"])
