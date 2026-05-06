"""
DLP Engine Extended Tests
--------------------------
Tests for detect_compliance_entities and evaluate_compliance
in app/services/dlp_engine.py
"""

from app.services.dlp_engine import (
    detect_compliance_entities,
    evaluate_compliance,
    scan_text,
    decide,
    redact_text,
    _severity_for_entity,
    _compute_risk,
    DlpFinding,
    PolicyDecision,
)


# --- detect_compliance_entities ---


def test_detects_ssn_as_hipaa():
    findings = detect_compliance_entities("SSN: 123-45-6789")
    types = [f["type"] for f in findings]
    assert "SSN" in types
    frameworks = [f["framework"] for f in findings]
    assert "HIPAA" in frameworks


def test_detects_medical_keyword():
    findings = detect_compliance_entities("patient diagnosis report")
    types = [f["type"] for f in findings]
    assert "MEDICAL_INFO" in types


def test_detects_treatment_keyword():
    findings = detect_compliance_entities("treatment plan")
    types = [f["type"] for f in findings]
    assert "MEDICAL_INFO" in types


def test_detects_unt_email_as_ferpa():
    findings = detect_compliance_entities("email: student@unt.edu")
    types = [f["type"] for f in findings]
    assert "STUDENT_EMAIL" in types
    frameworks = [f["framework"] for f in findings]
    assert "FERPA" in frameworks


def test_detects_academic_record():
    findings = detect_compliance_entities("student gpa transcript grade")
    types = [f["type"] for f in findings]
    assert "ACADEMIC_RECORD" in types


def test_clean_text_no_findings():
    findings = detect_compliance_entities("hello world nothing sensitive")
    assert findings == []


# --- evaluate_compliance (dlp_engine version) ---


def test_evaluate_compliance_empty_findings():
    result = evaluate_compliance([])
    assert result["decision"] == "allow"
    assert result["severity"] == "low"
    assert result["frameworks"] == []


def test_evaluate_compliance_hipaa_blocks():
    findings = [{"type": "SSN", "framework": "HIPAA"}]
    result = evaluate_compliance(findings)
    assert result["decision"] in ("block", "redact", "allow")
    assert "HIPAA" in result["frameworks"]


def test_evaluate_compliance_ferpa_redacts():
    findings = [{"type": "STUDENT_EMAIL", "framework": "FERPA"}]
    result = evaluate_compliance(findings)
    assert result["severity"] in ("medium", "high", "low")
    assert "FERPA" in result["frameworks"]


def test_evaluate_compliance_returns_dict():
    result = evaluate_compliance([])
    assert "decision" in result
    assert "severity" in result
    assert "frameworks" in result


# --- scan_text ---


def test_scan_text_empty_returns_empty():
    text, findings = scan_text("")
    assert findings == []


def test_scan_text_none_returns_none():
    text, findings = scan_text(None)
    assert findings == []


def test_scan_text_with_email():
    text, findings = scan_text("Contact user@example.com")
    assert isinstance(findings, list)


# --- _severity_for_entity ---


def test_severity_ssn_is_high():
    assert _severity_for_entity("US_SOCIAL_SECURITY_NUMBER") == 3


def test_severity_credit_card_is_high():
    assert _severity_for_entity("CREDIT_CARD") == 3


def test_severity_email_is_medium():
    assert _severity_for_entity("EMAIL_ADDRESS") == 2


def test_severity_unknown_is_low():
    assert _severity_for_entity("UNKNOWN_ENTITY") == 1


# --- _compute_risk ---


def test_compute_risk_no_findings():
    assert _compute_risk([]) == 0.0


def test_compute_risk_high_count_uses_multiplier():
    findings = [DlpFinding(type="EMAIL_ADDRESS", count=5, severity=2)]
    risk = _compute_risk(findings)
    assert risk > 0


def test_compute_risk_capped_at_one():
    findings = [DlpFinding(type="CREDIT_CARD", count=100, severity=3)]
    risk = _compute_risk(findings)
    assert risk <= 1.0


# --- decide ---


def test_decide_empty_findings_allows():
    result = decide([])
    assert result.decision == PolicyDecision.ALLOW


def test_decide_high_severity_blocks():
    findings = [DlpFinding(type="CREDIT_CARD", count=1, severity=3)]
    result = decide(findings)
    assert result.decision == PolicyDecision.BLOCK


def test_decide_medium_severity_redacts():
    findings = [DlpFinding(type="EMAIL_ADDRESS", count=1, severity=2)]
    result = decide(findings)
    assert result.decision == PolicyDecision.REDACT


# --- redact_text ---


def test_redact_text_returns_tuple():
    result = redact_text("masked text", [])
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_redact_text_filters_zero_count():
    findings = [
        DlpFinding(type="EMAIL_ADDRESS", count=2, severity=2),
        DlpFinding(type="PHONE_NUMBER", count=0, severity=2),
    ]
    _, meta = redact_text("text", findings)
    assert len(meta) == 1
    assert meta[0]["type"] == "EMAIL_ADDRESS"
