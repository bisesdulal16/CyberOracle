"""
DLP (Data Loss Prevention) Middleware
-------------------------------------
Purpose:
Intercepts incoming POST, PUT, and PATCH requests and scans them for
sensitive data such as SSNs, credit card numbers, emails, or API keys.
If detected, the values are redacted before the data reaches the
main application or database layer.


This version uses the central Presidio-based DLP engine plus custom patterns
from app.middleware.dlp_presidio, and triggers a single alert per request.
"""

import json
from typing import Any, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.middleware.dlp_presidio import presidio_scan
from app.utils.alert_manager import send_alert


def _sanitize_value(value: Any, detected_entities: Set[str]) -> Any:
    """
    Recursively sanitize a value:
    - If it's a string, run presidio_scan(alert=False) and collect entities.
    - If it's a dict or list, walk through and sanitize nested values.
    - Otherwise, return as-is.
    """
    if isinstance(value, str):
        redacted_text, entities = presidio_scan(value, alert=False)
        detected_entities.update(entities)
        return redacted_text

    if isinstance(value, dict):
        return {k: _sanitize_value(v, detected_entities) for k, v in value.items()}

    if isinstance(value, list):
        return [_sanitize_value(item, detected_entities) for item in value]

    return value


class DLPFilterMiddleware(BaseHTTPMiddleware):
    """
    Custom FastAPI middleware that scans and redacts sensitive data from
    incoming request bodies before they are processed by router handlers.
    """

    async def dispatch(self, request: Request, call_next):
        detected_entities: Set[str] = set()

        # Target only data-carrying methods
        if request.method in {"POST", "PUT", "PATCH"}:
            try:
                body = await request.json()
            except Exception:
                body = None

            if isinstance(body, dict):
                sanitized_body = _sanitize_value(body, detected_entities)

                # If anything was actually detected and redacted, replace request body
                if detected_entities:
                    request._body = json.dumps(sanitized_body).encode("utf-8")

        # If any entities were detected anywhere in the request, send one alert
        if detected_entities:
            message = "DLP Alert: Sensitive data detected in request — " + ", ".join(
                sorted(detected_entities)
            )

            send_alert(
                message,
                severity="high",
                source="dlp_middleware",
            )

        response = await call_next(request)
        return response
