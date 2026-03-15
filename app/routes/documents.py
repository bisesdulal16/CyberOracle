"""
Document Sanitizer Route
------------------------
Accepts PDF or DOCX file uploads, extracts text, runs regex-based DLP
redaction using the existing CyberOracle DLP engine, and returns the
sanitized text along with a breakdown of what was redacted.

Endpoint:
  POST /api/documents/sanitize
"""

import io
import os
import re

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from typing import List

from app.middleware.dlp_regex import REGEX_PATTERNS, scan_text

router = APIRouter(prefix="/api/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_MB = 10


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------


class RedactionFinding(BaseModel):
    type: str
    count: int


class SanitizeResponse(BaseModel):
    filename: str
    file_type: str
    total_redactions: int
    findings: List[RedactionFinding]
    redacted_text: str


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------


def _extract_text_pdf(content: bytes) -> str:
    """Extract plain text from a PDF using pdfplumber."""
    import pdfplumber  # lazy import — only needed when PDF is uploaded

    text_parts: List[str] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def _extract_text_docx(content: bytes) -> str:
    """Extract plain text from a DOCX using python-docx."""
    from docx import Document  # lazy import — only needed when DOCX is uploaded

    doc = Document(io.BytesIO(content))
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())


# ---------------------------------------------------------------------------
# Finding counter (runs on original text before redaction)
# ---------------------------------------------------------------------------


def _count_findings(text: str) -> List[RedactionFinding]:
    """
    Count regex matches per pattern type in the original text.
    Returns a list of RedactionFinding sorted by count descending.
    """
    findings: List[RedactionFinding] = []
    for name, pattern in REGEX_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            findings.append(RedactionFinding(type=name.upper(), count=len(matches)))
    return sorted(findings, key=lambda f: f.count, reverse=True)


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.post("/sanitize", response_model=SanitizeResponse)
async def sanitize_document(file: UploadFile = File(...)):
    """
    Upload a PDF or DOCX document for DLP scanning and redaction.

    - Validates file type (PDF and DOCX only)
    - Enforces 10 MB size limit
    - Extracts text and runs regex DLP (SSN, credit card, email, API keys)
    - Returns sanitized text and a findings breakdown
    """
    # --- Validate extension ---
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{ext}'. "
                "Only PDF (.pdf) and Word documents (.docx) are accepted."
            ),
        )

    # --- Read file content ---
    content = await file.read()

    # --- Enforce size limit ---
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE_MB} MB.",
        )

    # --- Extract text ---
    try:
        if ext == ".pdf":
            raw_text = _extract_text_pdf(content)
            file_type = "PDF"
        else:
            raw_text = _extract_text_docx(content)
            file_type = "DOCX"
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Could not extract text from the file: {exc}",
        )

    if not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail=(
                "No text content found in this file. "
                "The document may be image-only or password-protected."
            ),
        )

    # --- DLP scan ---
    findings = _count_findings(raw_text)
    redacted_text, _ = scan_text(raw_text)
    total_redactions = sum(f.count for f in findings)

    return SanitizeResponse(
        filename=filename,
        file_type=file_type,
        total_redactions=total_redactions,
        findings=findings,
        redacted_text=redacted_text,
    )
