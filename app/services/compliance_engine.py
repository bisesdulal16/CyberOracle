# app/services/compliance_engine.py

from typing import List, Dict


def evaluate_compliance(text: str, entities: List[str]) -> Dict[str, object]:
    text_lower = text.lower()
    frameworks = set()

    # HIPAA-like detection
    if "US_SOCIAL_SECURITY_NUMBER" in entities:
        frameworks.add("HIPAA")
    if any(
        word in text_lower for word in ["patient", "diagnosis", "treatment", "medical"]
    ):
        frameworks.add("HIPAA")

    # FERPA-like detection
    if any(
        word in text_lower
        for word in ["student", "student id", "gpa", "transcript", "grade"]
    ):
        frameworks.add("FERPA")
    if "@unt.edu" in text_lower:
        frameworks.add("FERPA")

    if "HIPAA" in frameworks:
        return {
            "frameworks": sorted(frameworks),
            "decision": "block",
            "severity": "high",
        }

    if "FERPA" in frameworks:
        return {
            "frameworks": sorted(frameworks),
            "decision": "redact",
            "severity": "medium",
        }

    return {
        "frameworks": [],
        "decision": "allow",
        "severity": "low",
    }
