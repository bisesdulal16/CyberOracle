"""
Standalone Regex-Based DLP Scanner
-----------------------------------

Purpose:
Provides a simple regex-based DLP engine for detecting sensitive data
such as SSNs, credit card numbers, emails, and API keys.

This is separate from the middleware. It will be used in:
- Week 2 tests
- Red-team dataset evaluation
- Comparison with Presidio (Week 3)
"""

import re
from typing import List, Dict

# ---------------------------
# Regex patterns for Week 2
# ---------------------------
REGEX_PATTERNS: Dict[str, str] = {
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    # Matches 13–16 digits, optional spaces/hyphens
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    # Generic API key — long alphanumeric string
    "api_key": r"\b[A-Za-z0-9]{20,}\b",
}


def scan_text(text: str):
    """
    Scan input text for sensitive data using regex rules.
    Returns sanitized text and list of detected entities.
    """

    detected: List[str] = []
    sanitized = text

    for name, pattern in REGEX_PATTERNS.items():
        matches = re.findall(pattern, sanitized)
        if matches:
            detected.append(name)
            sanitized = re.sub(pattern, f"<{name.upper()}>", sanitized)

    return sanitized, detected


# ---------------------------
# Optional CLI usage
# ---------------------------
if __name__ == "__main__":
    print("=== CyberOracle Regex-Based DLP Scanner ===")
    user_input = input("Enter text to scan: ")

    redacted, entities = scan_text(user_input)

    print("\nDetected:", entities)
    print("Redacted:", redacted)
