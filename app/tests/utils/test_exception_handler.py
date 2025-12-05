from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from fastapi.exceptions import RequestValidationError, HTTPException
from app.utils.exception_handler import secure_exception_handler


# -------------------------------------------------------
# Create a test FastAPI app with proper exception hooks
# -------------------------------------------------------
app = FastAPI()

# Attach custom handlers
app.add_exception_handler(Exception, secure_exception_handler)
app.add_exception_handler(RequestValidationError, secure_exception_handler)
app.add_exception_handler(HTTPException, secure_exception_handler)


# Schema to generate validation errors
class TestSchema(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=8)


@app.post("/validate")
def validate_payload(data: TestSchema):
    return {"ok": True}


# -------------------------------------------------------
# FIX: Make the endpoint async so FastAPI doesn't use the threadpool
# -------------------------------------------------------
@app.get("/boom")
async def boom():
    raise Exception("Password was: superSecret123!")  # Should be masked


client = TestClient(app)


# -------------------------------------------------------
# TEST 1 — Validation masking
# -------------------------------------------------------
def test_validation_error_masking():
    res = client.post("/validate", json={"username": "ab", "password": "short"})
    data = res.json()

    assert res.status_code == 422
    assert data["detail"] == "Input validation failed."
    assert isinstance(data["errors"], list)

    assert any("Username" in msg for msg in data["errors"])
    assert any("Password" in msg for msg in data["errors"])

    # Sensitive password must not appear
    assert "short" not in str(data)
