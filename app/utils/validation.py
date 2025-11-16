import re


def sanitize_input(value: str) -> str:
    """Remove dangerous characters."""
    if not isinstance(value, str):
        return value
    return re.sub(r"[<>\"';]", "", value)


def is_valid_length(value: str, max_len: int = 255) -> bool:
    """Ensure input doesn't exceed allowed lengths."""
    return isinstance(value, str) and len(value) <= max_len
