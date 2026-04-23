"""
Smoke tests for POST /api/documents/sanitize
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routes.documents as doc_module
from app.routes.documents import _count_findings
from app.auth.jwt_utils import create_access_token


@pytest.fixture
def client():
    application = FastAPI()
    application.include_router(doc_module.router)
    with patch.object(doc_module, "log_request", new=AsyncMock()):
        yield TestClient(application)


@pytest.fixture
def auth_headers():
    token = create_access_token({"sub": "test", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


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


def test_rejects_unsupported_extension(client, auth_headers):
    """Plain text files must be rejected with 400."""
    response = client.post(
        "/api/documents/sanitize",
        files={"file": ("report.txt", b"Some text content", "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_rejects_oversized_file(client, auth_headers):
    """Files over 10 MB must be rejected with 413."""
    oversized = b"x" * (11 * 1024 * 1024)
    response = client.post(
        "/api/documents/sanitize",
        files={
            "file": (
                "big.docx",
                oversized,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        headers=auth_headers,
    )
    assert response.status_code == 413


def test_sanitizes_docx_with_pii(client, auth_headers, monkeypatch):
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
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "patient_record.docx"
    assert data["file_type"] == "DOCX"
    assert data["total_redactions"] > 0
    assert len(data["findings"]) > 0
    assert "123-45-6789" not in data["redacted_text"]


def test_empty_document_returns_422(client, auth_headers, monkeypatch):
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
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_clean_document_returns_zero_redactions(client, auth_headers, monkeypatch):
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
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_redactions"] == 0
    assert data["findings"] == []


def test_extract_text_pdf_collects_page_text(monkeypatch):
    class FakePage:
        def __init__(self, text):
            self._text = text

        def extract_text(self):
            return self._text

    class FakePDF:
        def __init__(self):
            self.pages = [FakePage("Page one"), FakePage(None), FakePage("Page three")]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    import sys
    import types

    fake_pdfplumber = types.SimpleNamespace(open=lambda _stream: FakePDF())
    monkeypatch.setitem(sys.modules, "pdfplumber", fake_pdfplumber)

    result = doc_module._extract_text_pdf(b"fake-pdf-bytes")
    assert result == "Page one\n\nPage three"


def test_extract_text_docx_collects_non_empty_paragraphs(monkeypatch):
    class FakeParagraph:
        def __init__(self, text):
            self.text = text

    class FakeDocument:
        def __init__(self, _stream):
            self.paragraphs = [
                FakeParagraph("First paragraph"),
                FakeParagraph("   "),
                FakeParagraph("Second paragraph"),
            ]

    import sys
    import types

    fake_docx_module = types.SimpleNamespace(Document=FakeDocument)
    monkeypatch.setitem(sys.modules, "docx", fake_docx_module)

    result = doc_module._extract_text_docx(b"fake-docx-bytes")
    assert result == "First paragraph\nSecond paragraph"


def test_sanitizes_pdf_with_pii(client, auth_headers, monkeypatch):
    pii_text = "PDF text with SSN 123-45-6789 and email pdf@test.com"
    monkeypatch.setattr(doc_module, "_extract_text_pdf", lambda _content: pii_text)

    response = client.post(
        "/api/documents/sanitize",
        files={"file": ("record.pdf", b"fake-pdf-bytes", "application/pdf")},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["file_type"] == "PDF"
    assert data["total_redactions"] > 0
    assert "123-45-6789" not in data["redacted_text"]


def test_pdf_extraction_failure_returns_422(client, auth_headers, monkeypatch):
    """
    PDF extraction failure must return 422 with a safe error message.
    Internal exception details must not be exposed (NCFR6).
    """
    def _boom(_content):
        raise ValueError("parse failed")

    monkeypatch.setattr(doc_module, "_extract_text_pdf", _boom)

    response = client.post(
        "/api/documents/sanitize",
        files={"file": ("broken.pdf", b"fake-pdf-bytes", "application/pdf")},
        headers=auth_headers,
    )

    assert response.status_code == 422
    # NCFR6: Safe message — internal ValueError detail not exposed
    assert "Could not extract text" in response.json()["detail"]
    assert "parse failed" not in response.json()["detail"]