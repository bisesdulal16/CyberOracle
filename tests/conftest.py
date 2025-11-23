import pytest
from app.middleware.rate_limiter import reset_rate_limit_state


@pytest.fixture(autouse=True)
def clear_rate_limiter_state():
    reset_rate_limit_state()
    yield
    reset_rate_limit_state()
