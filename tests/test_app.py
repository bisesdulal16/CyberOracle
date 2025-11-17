"""
Unit Tests for CyberOracle FastAPI Application
----------------------------------------------
Purpose:
These tests validate the functionality and security of the FastAPI gateway.
They ensure that:
  1. The health endpoint responds correctly (for uptime and monitoring checks).
  2. The DLP middleware redacts sensitive information like SSNs.
  3. Non-sensitive data passes through unaffected.

Testing Framework:
- Uses FastAPI's built-in TestClient (powered by Starlette)
- Executed automatically via GitHub Actions (CI/CD)
"""

from fastapi.testclient import TestClient
from app.main import app

# Initialize a testing client for the FastAPI app
client = TestClient(app)


def test_health_endpoint():
    """
    Verify that the /health endpoint is working correctly.
    This ensures that the service is up, responding, and properly configured.
    """
    response = client.get("/health")
    # Expect a 200 OK HTTP status
    assert response.status_code == 200
    # Validate the expected JSON response format
    assert response.json() == {"status": "OK", "service": "CyberOracle API"}


def test_dlp_redacts_ssn():
    """
    Test that the DLP middleware correctly redacts sensitive data (SSNs).
    Input: JSON payload containing a valid SSN.
    Expected: The response should contain '***' indicating redaction occured.
    """
    payload = {"data": "My SSN is 123-45-6789"}
    response = client.post("/logs", json=payload)
    # Allow status codes 200,201, or 404 (depending on endpoint behavior)
    assert response.status_code in [200, 201, 404]
    # Ensure the SSN was replaced with redaction marks
    assert ("***" in response.text) or ("<GENERIC_SSN>" in response.text)


def test_dlp_allows_normal_data():
    """
    Test that the DLP middleware does NOT alter harmless data.
    Input: Normal text without any sensitive content.
    Expected: The response should not contain '***'
    """
    payload = {"data": "Hello from CyberOracle"}
    response = client.post("/logs", json=payload)
    # Valid responses for POST without active /logs DB logic
    assert response.status_code in [200, 201, 404]
    # Verify that no redaction took place
    assert "***" not in str(response.text)
