from app.services import dlp_engine
from app.services.dlp_engine import DlpFinding, PolicyDecision


def test_scan_text_no_findings():
    redacted, findings = dlp_engine.scan_text("hello world")
    assert isinstance(redacted, str)
    assert findings == []


def test_scan_text_detects_email():
    redacted, findings = dlp_engine.scan_text("email me at test@example.com")
    assert "example.com" not in redacted
    assert len(findings) >= 1
    assert any(
        f.type.lower() in ("email", "email_address", "email_address_regex")
        or "email" in f.type.lower()
        for f in findings
    )


def test_decide_allow_when_empty():
    decision = dlp_engine.decide([])
    assert decision.decision == PolicyDecision.ALLOW


def test_redact_text_returns_string_and_meta():
    redacted, findings = dlp_engine.scan_text("contact test@example.com")
    out_text, meta = dlp_engine.redact_text(redacted, findings)
    assert isinstance(out_text, str)
    assert isinstance(meta, list)


def test_severity_for_entity_high():
    assert dlp_engine._severity_for_entity("US_SOCIAL_SECURITY_NUMBER") == 3
    assert dlp_engine._severity_for_entity("CREDIT_CARD") == 3


def test_severity_for_entity_medium():
    assert dlp_engine._severity_for_entity("EMAIL_ADDRESS") == 2
    assert dlp_engine._severity_for_entity("PHONE_NUMBER") == 2


def test_severity_for_entity_default_low():
    assert dlp_engine._severity_for_entity("SOME_UNKNOWN_ENTITY") == 1


def test_compute_risk_empty():
    assert dlp_engine._compute_risk([]) == 0.0


def test_compute_risk_with_count_under_5():
    findings = [DlpFinding(type="EMAIL_ADDRESS", count=1, severity=2)]
    assert dlp_engine._compute_risk(findings) == 0.1


def test_compute_risk_with_count_5_or_more_uses_multiplier():
    findings = [DlpFinding(type="EMAIL_ADDRESS", count=5, severity=2)]
    assert dlp_engine._compute_risk(findings) == 0.15


def test_decide_block_for_high_severity():
    findings = [DlpFinding(type="CREDIT_CARD", count=1, severity=3)]
    decision = dlp_engine.decide(findings)

    assert decision.decision == PolicyDecision.BLOCK
    assert decision.findings == findings
    assert decision.risk_score > 0


def test_decide_redact_for_medium_severity():
    findings = [DlpFinding(type="EMAIL_ADDRESS", count=1, severity=2)]
    decision = dlp_engine.decide(findings)

    assert decision.decision == PolicyDecision.REDACT
    assert decision.findings == findings


def test_decide_allow_for_low_severity():
    findings = [DlpFinding(type="GENERIC_TEXT", count=1, severity=1)]
    decision = dlp_engine.decide(findings)

    assert decision.decision == PolicyDecision.ALLOW
    assert decision.findings == findings


def test_decide_high_risk_override_to_redact():
    findings = [
        DlpFinding(type="EMAIL_ADDRESS", count=5, severity=2),
        DlpFinding(type="PHONE_NUMBER", count=5, severity=2),
        DlpFinding(type="PERSON", count=5, severity=2),
        DlpFinding(type="MEDIUM_A", count=5, severity=2),
        DlpFinding(type="MEDIUM_B", count=5, severity=2),
        DlpFinding(type="MEDIUM_C", count=5, severity=2),
    ]
    decision = dlp_engine.decide(findings)

    assert decision.risk_score > 0.85
    assert decision.decision == PolicyDecision.REDACT


def test_redact_text_filters_zero_count_findings():
    findings = [
        DlpFinding(type="EMAIL_ADDRESS", count=2, severity=2),
        DlpFinding(type="PHONE_NUMBER", count=0, severity=2),
    ]

    out_text, meta = dlp_engine.redact_text("masked text", findings)

    assert out_text == "masked text"
    assert meta == [{"type": "EMAIL_ADDRESS", "count": 2}]
