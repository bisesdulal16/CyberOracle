"""
Standalone Regex-Based DLP Scanner
-----------------------------------

Purpose:
Provides a regex-based DLP engine for detecting sensitive data
such as SSNs, credit card numbers, emails, and API keys.

Used in:
- Document sanitizer
- Red-team dataset evaluation
- Comparison baseline against Presidio

OWASP API Security:
- Prevents sensitive data from being stored or transmitted.
- All patterns validated against real-world PII formats.
"""

import re
from typing import List, Dict, Tuple

# ---------------------------------------------------------------------------
# Regex patterns — validated against real-world PII formats
# ---------------------------------------------------------------------------
REGEX_PATTERNS: Dict[str, str] = {
    # US Social Security Numbers: XXX-XX-XXXX
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    # Credit cards — major card types only (reduces false positives)
    # Visa: 4XXXXXXXXXXXXXXX (13 or 16 digits)
    # Mastercard: 5[1-5]XXXXXXXXXXXXXX (16 digits)
    # Amex: 3[47]XXXXXXXXXXXXX (15 digits)
    # Discover: 6(?:011|5XX)XXXXXXXXXXXX (16 digits)
    "credit_card": (
        r"\b(?:"
        r"4[0-9]{3}(?:[ -]?[0-9]{4}){3}"  # Visa
        r"|5[1-5][0-9]{2}(?:[ -]?[0-9]{4}){3}"  # Mastercard
        r"|3[47][0-9]{2}(?:[ -]?[0-9]{4}){2}[0-9]{3}"  # Amex
        r"|6(?:011|5[0-9]{2})(?:[ -]?[0-9]{4}){3}"  # Discover
        r")\b"
    ),
    # Email addresses
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    # API keys — must have key/token prefix to reduce false positives
    # Matches: api_key=XXXX, apikey: XXXX, sk-XXXX, AKIA... (AWS)
    "api_key": (
        r"(?i)(?:api[_-]?key|apikey|api[_-]?token|secret[_-]?key)"
        r"[\s:=]+['\"]?([A-Za-z0-9_\-]{16,})['\"]?"
        r"|(?:sk-|AKIA)[A-Za-z0-9]{16,}"
    ),
}


def scan_text(text: str) -> Tuple[str, List[str]]:
    """
    Scan input text for sensitive data using regex rules.

    Parameters
    ----------
    text : str
        Input text to scan.

    Returns
    -------
    sanitized : str
        Text with sensitive values replaced by placeholders.
    detected : List[str]
        List of entity type names that were detected.
    """
    if not text:
        return text, []

    detected: List[str] = []
    sanitized = text

    for name, pattern in REGEX_PATTERNS.items():
        matches = re.findall(pattern, sanitized)
        if matches:
            detected.append(name)
            sanitized = re.sub(pattern, f"<{name.upper()}>", sanitized)

    return sanitized, detected


# ---------------------------------------------------------------------------
# Optional CLI usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== CyberOracle Regex-Based DLP Scanner ===")
    user_input = input("Enter text to scan: ")
    redacted, entities = scan_text(user_input)
    print("\nDetected:", entities)
    print("Redacted:", redacted)
