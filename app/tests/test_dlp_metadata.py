#!/usr/bin/env python3
"""
Test script to verify DLP metadata is correctly passed from middleware to routes
"""

import asyncio
from unittest.mock import AsyncMock, Mock
from app.middleware.dlp_filter import DLPFilterMiddleware
from app.main import app


# Test the middleware behavior
async def test_dlp_middleware_metadata():
    """Test that middleware correctly sets DLP metadata on request.state"""

    # Create a mock request with sensitive data
    request = Mock()
    request.method = "POST"
    request.json = Mock(return_value={"prompt": "My SSN is 123-45-6789"})
    request._body = b'{"prompt": "My SSN is 123-45-6789"}'

    # Mock the call_next function
    call_next = AsyncMock()
    call_next.return_value = Mock()

    # Create middleware instance
    middleware = DLPFilterMiddleware(app)

    # Test that middleware sets the DLP metadata
    await middleware.dispatch(request, call_next)

    # Check that metadata was set
    assert hasattr(request.state, "dlp_detected")
    assert hasattr(request.state, "dlp_entities")
    assert hasattr(request.state, "dlp_redacted")
    assert hasattr(request.state, "dlp_policy_decision")
    assert hasattr(request.state, "dlp_risk_score")
    assert hasattr(request.state, "dlp_severity")

    print("✅ DLP middleware correctly sets metadata on request.state")
    print(f"dlp_detected: {request.state.dlp_detected}")
    print(f"dlp_entities: {request.state.dlp_entities}")
    print(f"dlp_redacted: {request.state.dlp_redacted}")
    print(f"dlp_policy_decision: {request.state.dlp_policy_decision}")
    print(f"dlp_risk_score: {request.state.dlp_risk_score}")
    print(f"dlp_severity: {request.state.dlp_severity}")


if __name__ == "__main__":
    asyncio.run(test_dlp_middleware_metadata())
