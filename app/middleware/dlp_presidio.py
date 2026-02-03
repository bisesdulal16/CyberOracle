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
    "PHONE_NUMBER",  # for tests
    "PERSON",  # for tests
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

# --- Generic SSN ---
ssn_pattern = Pattern(
    name="Generic SSN",
    regex=r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b",
    score=0.7,
)
ssn_recognizer = PatternRecognizer(
    supported_entity="GENERIC_SSN",
    patterns=[ssn_pattern],
    context=["ssn", "social", "security", "number", "identity", "tax"],
)

# ---------------------------------------------------------------------
# Initialize engines
# ---------------------------------------------------------------------
analyzer = AnalyzerEngine()
analyzer.registry.add_recognizer(api_key_recognizer)
analyzer.registry.add_recognizer(ssn_recognizer)
anonymizer = AnonymizerEngine()


def presidio_scan(text: str, alert: bool = True):
    """
    Analyze and anonymize text using Microsoft Presidio with restricted entity set.
    Optionally sends alert if any PII/PHI entity is detected (alert=True).
    Returns:
        anonymized_text (str), entities (List[str])
    """
    results = analyzer.analyze(text=text, entities=TARGET_ENTITIES, language="en")

    if results and alert:
        entity_types = sorted({r.entity_type for r in results})
        send_alert(
            f"DLP Alert: Sensitive data detected — {', '.join(entity_types)}",
            severity="high",
            source="presidio_dlp",
        )

    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text, [r.entity_type for r in results]
