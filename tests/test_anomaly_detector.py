from httpx import AsyncClient
from app.main import app
from app.utils.alert_manager import send_alert

import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_large_payload_triggers_alert():
    large_text = "A" * (6 * 1024)  # 6 KB payload
    payload = {"data": large_text}

    with patch("app.middleware.anomaly_detector.send_alert") as mock_alert:
        async with AsyncClient(app=app, base_url="http://test") as client:
            await client.post("/logs", json=payload)

        mock_alert.assert_called_once()


@pytest.mark.asyncio
async def test_suspicious_keyword_triggers_alert():
    payload = {"data": "DROP TABLE users;"}

    with patch("app.middleware.anomaly_detector.send_alert") as mock_alert:
        async with AsyncClient(app=app, base_url="http://test") as client:
            await client.post("/logs", json=payload)

        mock_alert.assert_called_once()


@pytest.mark.asyncio
async def test_rate_limit_triggers_alert():
    payload = {"data": "normal"}

    with patch("app.middleware.anomaly_detector.send_alert") as mock_alert:
        async with AsyncClient(app=app, base_url="http://test") as client:
            for _ in range(7):  # trigger >5/10s threshold
                await client.post("/logs", json=payload)

        assert mock_alert.called
