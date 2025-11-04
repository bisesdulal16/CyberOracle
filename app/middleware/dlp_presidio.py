"""
dlp_presidio.py
---------------
CyberOracle DLP module integrating Microsoft Presidio for PII detection.
Includes restricted entity set and custom recognizers for API keys and SSNs.
"""

from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine

# Restrict to the entities we care about for MVP accuracy
TARGET_ENTITIES = [
    "US_SOCIAL_SECURITY_NUMBER",
    "GENERIC_SSN",
    "CREDIT_CARD",
    "EMAIL_ADDRESS",
    "GENERIC_API_KEY",
]

# --- Custom recognizer: API keys / tokens ---
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

# --- Custom recognizer: Generic SSNs (lenient) ---
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

# Initialize analyzer and anonymizer
analyzer = AnalyzerEngine()
analyzer.registry.add_recognizer(api_key_recognizer)
analyzer.registry.add_recognizer(ssn_recognizer)

anonymizer = AnonymizerEngine()


def presidio_scan(text: str):
    """
    Analyze and anonymize text using Microsoft Presidio with a restricted entity set.
    """
    results = analyzer.analyze(text=text, entities=TARGET_ENTITIES, language="en")
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text, [r.entity_type for r in results]
