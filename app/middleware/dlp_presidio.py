"""
CyberOracle DLP Module — Microsoft Presidio Integration
--------------------------------------------------------
Detects and redacts sensitive data (SSN, credit card, email, API key)
and triggers real-time Discord alerts when found.
"""

from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from app.utils.alert_manager import send_alert

# ---------------------------------------------------------------------
# Target entity types for MVP phase (restricted scope)
# ---------------------------------------------------------------------
TARGET_ENTITIES = [
    "US_SOCIAL_SECURITY_NUMBER",
    "GENERIC_SSN",
    "CREDIT_CARD",
    "EMAIL_ADDRESS",
    "GENERIC_API_KEY",
    "PHONE_NUMBER",
    "PERSON",
    "LOCATION",
    "DATE_TIME",
    "IP_ADDRESS",
    "US_PASSPORT",
    "US_DRIVER_LICENSE",
    "US_BANK_NUMBER",
    "MEDICAL_LICENSE",
    "URL",
    "NRP",
]

# ---------------------------------------------------------------------
# Custom recognizers for higher accuracy
# ---------------------------------------------------------------------

# --- API Keys (common patterns like api_key=XXXXXX) ---
api_key_pattern = Pattern(
    name="Generic API key",
    regex=r'(?i)(api[_-]?key|apikey|api[_-]?token)[\s:=]+["\']?([A-Za-z0-9_-]{20,})["\']?',
    score=0.7,
)
api_key_recognizer = PatternRecognizer(
    supported_entity="GENERIC_API_KEY",
    patterns=[api_key_pattern],
    context=["api", "key", "token", "apikey", "api_key", "api-token"],
)

# --- Generic SSN (requires dashes to avoid false-positive on bank numbers) ---
ssn_pattern = Pattern(
    name="Generic SSN",
    regex=r"\b\d{3}-\d{2}-\d{4}\b",
    score=0.85,
)
ssn_recognizer = PatternRecognizer(
    supported_entity="GENERIC_SSN",
    patterns=[ssn_pattern],
    context=["ssn", "social", "security", "number", "identity", "tax"],
)

# --- Phone numbers ---
phone_pattern = Pattern(
    name="US Phone",
    regex=r"\b(?:\+1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b",
    score=0.7,
)
phone_recognizer = PatternRecognizer(
    supported_entity="PHONE_NUMBER",
    patterns=[phone_pattern],
    context=["phone", "call", "mobile", "contact", "reach"],
)

# --- IP addresses ---
ip_pattern = Pattern(
    name="IPv4 Address",
    regex=r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
    score=0.7,
)
ip_recognizer = PatternRecognizer(
    supported_entity="IP_ADDRESS",
    patterns=[ip_pattern],
    context=["ip", "address", "host", "server", "network", "internal"],
)

# --- Bank account numbers ---
bank_pattern = Pattern(
    name="Bank Account",
    regex=r"(?i)(?:account|acct|routing)[\s#:]+[0-9]{8,17}",
    score=0.75,
)
bank_recognizer = PatternRecognizer(
    supported_entity="US_BANK_NUMBER",
    patterns=[bank_pattern],
    context=["bank", "account", "routing", "acct", "payroll"],
)

# ---------------------------------------------------------------------
# Initialize engines
# ---------------------------------------------------------------------
analyzer = AnalyzerEngine()
analyzer.registry.add_recognizer(api_key_recognizer)
analyzer.registry.add_recognizer(ssn_recognizer)
analyzer.registry.add_recognizer(phone_recognizer)
analyzer.registry.add_recognizer(ip_recognizer)
analyzer.registry.add_recognizer(bank_recognizer)
anonymizer = AnonymizerEngine()


def presidio_scan(text: str, alert: bool = True):
    """
    Analyze and anonymize text using Microsoft Presidio with restricted entity set.
    Optionally sends alert if any PII/PHI entity is detected (alert=True).
    Returns:
        anonymized_text (str), entities (List[str])
    """
    results = analyzer.analyze(
        text=text, entities=TARGET_ENTITIES, language="en", score_threshold=0.3
    )

    if results and alert:
        entity_types = sorted({r.entity_type for r in results})
        send_alert(
            f"DLP Alert: Sensitive data detected — {', '.join(entity_types)}",
            severity="high",
            source="presidio_dlp",
        )

    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text, [r.entity_type for r in results]
