"""
Smoke tests for POST /api/documents/sanitize

These tests mount only the documents router so no DB or Presidio is needed.
File parsing (pdfplumber / python-docx) is monkeypatched in the DLP test so
the suite runs without the optional extraction libraries installed.
"""

import io
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routes.documents as doc_module
from app.routes.documents import _count_findings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Minimal FastAPI app mounting only the documents router."""
    application = FastAPI()
    application.include_router(doc_module.router)
    return TestClient(application)


# ---------------------------------------------------------------------------
# Unit tests — _count_findings (no HTTP, no file parsing)
# ---------------------------------------------------------------------------

def test_count_findings_detects_ssn():
    findings = _count_findings("Patient SSN is 123-45-6789.")
    types = [f.type for f in findings]
    assert "SSN" in types


def test_count_findings_detects_email():
    findings = _count_findings("Contact admin@example.com for support.")
    types = [f.type for f in findings]
    assert "EMAIL" in types


def test_count_findings_clean_text():
    findings = _count_findings("This document contains no sensitive information.")
    assert findings == []


def test_count_findings_multiple_types():
    text = "SSN: 123-45-6789. Email: user@test.com."
    findings = _count_findings(text)
    types = [f.type for f in findings]
    assert "SSN" in types
    assert "EMAIL" in types


# ---------------------------------------------------------------------------
# Integration tests — HTTP endpoint
# ---------------------------------------------------------------------------

def test_rejects_unsupported_extension(client):
    """Plain text files must be rejected with 400."""
    response = client.post(
        "/api/documents/sanitize",
        files={"file": ("report.txt", b"Some text content", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_rejects_oversized_file(client):
    """Files over 10 MB must be rejected with 413."""
    oversized = b"x" * (11 * 1024 * 1024)  # 11 MB
    response = client.post(
        "/api/documents/sanitize",
        files={"file": ("big.docx", oversized, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 413


def test_sanitizes_docx_with_pii(client, monkeypatch):
    """
    DOCX with PII should return redacted text and non-zero findings.
    The DOCX extraction is monkeypatched to return a known string so
    this test runs without python-docx installed.
    """
    pii_text = (
        "Patient John Doe, SSN 123-45-6789, "
        "email john.doe@hospital.org, "
        "card 4111 1111 1111 1111."
    )

    monkeypatch.setattr(doc_module, "_extract_text_docx", lambda _content: pii_text)

    response = client.post(
        "/api/documents/sanitize",
        files={
            "file": (
                "patient_record.docx",
                b"fake-docx-bytes",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "patient_record.docx"
    assert data["file_type"] == "DOCX"
    assert data["total_redactions"] > 0
    assert len(data["findings"]) > 0
    # Redacted text should not contain the original SSN
    assert "123-45-6789" not in data["redacted_text"]


def test_empty_document_returns_422(client, monkeypatch):
    """A DOCX with no extractable text should return 422."""
    monkeypatch.setattr(doc_module, "_extract_text_docx", lambda _content: "   ")

    response = client.post(
        "/api/documents/sanitize",
        files={
            "file": (
                "empty.docx",
                b"fake-docx-bytes",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 422


def test_clean_document_returns_zero_redactions(client, monkeypatch):
    """A document with no PII should return total_redactions = 0."""
    monkeypatch.setattr(
        doc_module,
        "_extract_text_docx",
        lambda _content: "This quarterly report covers general business operations.",
    )

    response = client.post(
        "/api/documents/sanitize",
        files={
            "file": (
                "clean.docx",
                b"fake-docx-bytes",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_redactions"] == 0
    assert data["findings"] == []
