"""
Input Validation Utilities
--------------------------
Simple sanitization and type-safety utilities.
Week 2 Deliverable — Niall Chiweshe
"""


def is_non_empty_string(value):
    return isinstance(value, str) and value.strip() != ""


def validate_text_field(payload: dict):
    """Ensure payload contains a non-empty 'text' field."""
    if "text" not in payload:
        return False
    return is_non_empty_string(payload["text"])
