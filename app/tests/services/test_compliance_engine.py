"""
Compliance Engine Tests
------------------------
Tests for evaluate_compliance() — HIPAA, FERPA detection.
"""

from app.services.compliance_engine import evaluate_compliance


def test_allow_clean_text():
    result = evaluate_compliance("hello world", [])
    assert result["decision"] == "allow"
    assert result["severity"] == "low"
    assert result["frameworks"] == []


def test_hipaa_triggered_by_ssn_entity():
    result = evaluate_compliance("some text", ["US_SOCIAL_SECURITY_NUMBER"])
    assert result["decision"] == "block"
    assert result["severity"] == "high"
    assert "HIPAA" in result["frameworks"]


def test_hipaa_triggered_by_medical_keyword():
    result = evaluate_compliance("patient diagnosis report", [])
    assert result["decision"] == "block"
    assert "HIPAA" in result["frameworks"]


def test_hipaa_triggered_by_treatment_keyword():
    result = evaluate_compliance("treatment plan for user", [])
    assert result["decision"] == "block"


def test_ferpa_triggered_by_student_keyword():
    result = evaluate_compliance("student gpa transcript", [])
    assert result["decision"] == "redact"
    assert result["severity"] == "medium"
    assert "FERPA" in result["frameworks"]


def test_ferpa_triggered_by_unt_email():
    result = evaluate_compliance("email is user@unt.edu", [])
    assert result["decision"] == "redact"
    assert "FERPA" in result["frameworks"]


def test_hipaa_takes_priority_over_ferpa():
    result = evaluate_compliance("patient student transcript", [])
    assert result["decision"] == "block"
    assert result["severity"] == "high"


def test_multiple_frameworks_returned():
    result = evaluate_compliance("patient student", [])
    assert len(result["frameworks"]) >= 1
