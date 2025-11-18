import os
import pytest
from app.middleware.rate_limiter import requests_log

os.environ["PYTEST"] = "1"
os.environ.setdefault("DISABLE_RATE_LIMIT_TEST", "0")


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter state before each test."""
    requests_log.clear()
