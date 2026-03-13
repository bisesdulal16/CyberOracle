# app/tests/services/test_dlp_engine.py
from app.services import dlp_engine
from app.services.dlp_engine import PolicyDecision


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
    # If your redact_text expects findings from scan_text, use that.
    redacted, findings = dlp_engine.scan_text("contact test@example.com")
    out_text, meta = dlp_engine.redact_text(redacted, findings)
    assert isinstance(out_text, str)
    assert isinstance(meta, list)
