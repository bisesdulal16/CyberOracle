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
    # Credit cards — Visa, Mastercard, Amex, Discover
    "credit_card": (
        r"\b(?:"
        r"4[0-9]{3}(?:[ -]?[0-9]{4}){3}"
        r"|5[1-5][0-9]{2}(?:[ -]?[0-9]{4}){3}"
        r"|3[47][0-9]{2}(?:[ -]?[0-9]{4}){2}[0-9]{3}"
        r"|6(?:011|5[0-9]{2})(?:[ -]?[0-9]{4}){3}"
        r")\b"
    ),
    # Email addresses
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    # API keys — api_key=XXXX, sk-XXXX, AKIA... (AWS)
    "api_key": (
        r"(?i)(?:api[_-]?key|apikey|api[_-]?token|secret[_-]?key)"
        r"[\s:=]+['\"]?([A-Za-z0-9_\-]{16,})['\"]?"
        r"|(?:sk-|AKIA)[A-Za-z0-9]{16,}"
    ),
    # US Phone numbers: (555) 123-4567, 555-123-4567, +1-555-123-4567
    "phone_number": (
        r"\b(?:\+1[-.\s]?)?" r"(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b"
    ),
    # US Passport numbers: letter + 8 digits
    "passport": r"\b[A-Z]{1}[0-9]{8}\b",
    # US Driver's License (generic: 1-2 letters + 6-8 digits)
    "drivers_license": r"\b[A-Z]{1,2}[0-9]{6,8}\b",
    # IP addresses (IPv4)
    "ip_address": (
        r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)"
        r"\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
    ),
    # Bank account numbers (8-17 digits with context)
    "bank_account": (r"(?i)(?:account|acct|routing)[\s#:]+([0-9]{8,17})"),
    # Date of birth patterns: MM/DD/YYYY or YYYY-MM-DD
    "date_of_birth": (
        r"(?i)(?:dob|date\s+of\s+birth|born\s+on)[\s:]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
        r"|\b\d{4}-\d{2}-\d{2}\b"
    ),
    # Medical Record Numbers (MRN)
    "medical_record": r"(?i)(?:mrn|medical\s+record|patient\s+id)[\s:#]+([A-Z0-9]{5,12})",
    # GitHub/GitLab tokens
    "git_token": r"(?:ghp_|gho_|ghs_|gitlab-)[A-Za-z0-9]{20,}",
    # AWS secret access key
    "aws_secret": r"(?i)aws[_-]?secret[_-]?(?:access[_-]?)?key[\s:=]+[A-Za-z0-9/+=]{40}",
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
