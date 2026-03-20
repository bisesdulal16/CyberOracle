# app/services/dlp_engine.py
"""
Central DLP Engine for CyberOracle
----------------------------------
Uses the shared Presidio analyzer/anonymizer plus a simple
decision + risk model.

This is used by:
- /ai/query (input + output scanning)
- /api/scan (if you add one later)
- any other internal services that need DLP.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Tuple

from app.middleware.dlp_presidio import analyzer, anonymizer, TARGET_ENTITIES
from app.policies.compliance_policies import COMPLIANCE_POLICIES


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    REDACT = "redact"
    BLOCK = "block"


@dataclass
class DlpFinding:
    type: str
    count: int
    severity: int  # 1=low, 2=medium, 3=high


@dataclass
class DlpDecision:
    decision: PolicyDecision
    risk_score: float
    findings: List[DlpFinding]


def _severity_for_entity(entity_type: str) -> int:
    """
    Map Presidio entity types to a coarse severity level.
    Tune this as you expand coverage.
    """
    high = {
        "US_SOCIAL_SECURITY_NUMBER",
        "GENERIC_SSN",
        "CREDIT_CARD",
        "GENERIC_API_KEY",
    }
    medium = {
        "EMAIL_ADDRESS",
        "PHONE_NUMBER",
        "PERSON",
    }

    if entity_type in high:
        return 3
    if entity_type in medium:
        return 2
    return 1


def scan_text(text: str) -> Tuple[str, List[DlpFinding]]:
    """
    Analyze + anonymize the text.

    Returns:
        redacted_text: the anonymized string
        findings: structured findings with counts & severity
    """
    if not text:
        return text, []

    results = analyzer.analyze(
        text=text,
        entities=TARGET_ENTITIES,
        language="en",
    )

    entities = [r.entity_type for r in results]
    counts = Counter(entities)

    findings: List[DlpFinding] = [
        DlpFinding(type=etype, count=cnt, severity=_severity_for_entity(etype))
        for etype, cnt in counts.items()
    ]

    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text, findings


def _compute_risk(findings: List[DlpFinding]) -> float:
    """
    Very simple risk model: sum severity*count and squash into [0,1].
    """
    if not findings:
        return 0.0

    score = 0.0
    for f in findings:
        mult = 1.0
        if f.count >= 5:
            mult = 1.5
        score += f.severity * mult

    # Normalize assuming ~20 is "max expected"
    return min(score / 20.0, 1.0)


def decide(findings: List[DlpFinding]) -> DlpDecision:
    """
    Map findings -> policy decision + risk_score.

    Policy:
    - Any severity 3 -> BLOCK
    - Otherwise any severity 2 -> REDACT
    - Otherwise -> ALLOW
    """
    risk = _compute_risk(findings)
    max_sev = max((f.severity for f in findings), default=0)

    if max_sev >= 3:
        decision = PolicyDecision.BLOCK
    elif max_sev == 2:
        decision = PolicyDecision.REDACT
    else:
        decision = PolicyDecision.ALLOW

    # If risk is extremely high but we didn't already block, at least redact
    if risk > 0.85 and decision != PolicyDecision.BLOCK:
        decision = PolicyDecision.REDACT

    return DlpDecision(decision=decision, risk_score=risk, findings=findings)


def redact_text(
    redacted_text: str, findings: List[DlpFinding]
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    We already get the anonymized text from scan_text, so here we just
    convert findings into the redactions metadata shape the UI expects.
    """
    redactions = [{"type": f.type, "count": f.count} for f in findings if f.count > 0]
    return redacted_text, redactions

def detect_compliance_entities(text: str):
    findings = []

    # HIPAA patterns
    if re.search(r"\b\d{3}-\d{2}-\d{4}\b", text):
        findings.append({"type": "SSN", "framework": "HIPAA"})

    if any(word in text.lower() for word in ["patient", "diagnosis", "treatment", "medical"]):
        findings.append({"type": "MEDICAL_INFO", "framework": "HIPAA"})

    # FERPA patterns
    if re.search(r"\b[\w.-]+@unt\.edu\b", text):
        findings.append({"type": "STUDENT_EMAIL", "framework": "FERPA"})

    if any(word in text.lower() for word in ["student id", "gpa", "transcript", "grade"]):
        findings.append({"type": "ACADEMIC_RECORD", "framework": "FERPA"})

    return findings

def evaluate_compliance(findings):
    frameworks = list(set(f["framework"] for f in findings))

    if not frameworks:
        return {
            "decision": "allow",
            "severity": "low",
            "frameworks": []
        }

    # prioritize highest severity
    for fw in frameworks:
        policy = COMPLIANCE_POLICIES[fw]

        if policy["severity"] == "high":
            return {
                "decision": policy["action"],
                "severity": "high",
                "frameworks": frameworks
            }

    return {
        "decision": "redact",
        "severity": "medium",
        "frameworks": frameworks
    }
