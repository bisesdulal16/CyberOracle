"""
Document Sanitizer Route
------------------------
Accepts PDF or DOCX file uploads, extracts text, runs regex-based DLP
redaction using the existing CyberOracle DLP engine, and returns the
sanitized text along with a breakdown of what was redacted.

Input validation:
- File type restricted to PDF and DOCX only
- File size limited to 10 MB
- Filename sanitized to prevent path traversal attacks
OWASP API3: Broken Object Property Level Authorization
"""

import io
import os
import re

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from typing import List

from app.auth.rbac import require_roles
from app.middleware.dlp_regex import REGEX_PATTERNS, scan_text
from app.utils.logger import log_request

router = APIRouter(prefix="/api/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_MB = 10

# Filename sanitization pattern — allow only safe characters
# OWASP API3: Prevents path traversal via malicious filenames
SAFE_FILENAME_PATTERN = re.compile(r"[^\w\s\-\.]")


class RedactionFinding(BaseModel):
    type: str
    count: int


class SanitizeResponse(BaseModel):
    filename: str
    file_type: str
    total_redactions: int
    findings: List[RedactionFinding]
    redacted_text: str


def _sanitize_filename(filename: str) -> str:
    """
    Strip path components and dangerous characters from filename.
    Prevents directory traversal and injection via filename.
    OWASP API3: Input validation on file metadata.
    """
    # Strip any directory components first
    base = os.path.basename(filename)
    # Remove any characters that aren't alphanumeric, spaces, hyphens, underscores, or dots
    safe = SAFE_FILENAME_PATTERN.sub("", base)
    # Limit length
    safe = safe[:255]
    return safe if safe else "uploaded_file"


def _extract_text_pdf(content: bytes) -> str:
    """Extract plain text from a PDF using pdfplumber."""
    import pdfplumber

    text_parts: List[str] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def _extract_text_docx(content: bytes) -> str:
    """Extract plain text from a DOCX using python-docx."""
    from docx import Document

    doc = Document(io.BytesIO(content))
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())


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


@router.post("/sanitize", response_model=SanitizeResponse)
async def sanitize_document(
    file: UploadFile = File(...),
    _user: dict = Depends(require_roles("admin", "developer")),
):
    """
    Upload a PDF or DOCX document for DLP scanning and redaction.

    - Validates and sanitizes filename (path traversal prevention)
    - Validates file type (PDF and DOCX only)
    - Enforces 10 MB size limit
    - Extracts text and runs regex DLP (SSN, credit card, email, API keys)
    - Returns sanitized text and a findings breakdown
    """
    # Sanitize filename — strip path traversal and dangerous characters
    raw_filename = file.filename or ""
    filename = _sanitize_filename(raw_filename)

    # Validate extension
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{ext}'. "
                "Only PDF (.pdf) and Word documents (.docx) are accepted."
            ),
        )

    # Read and enforce size limit
    content = await file.read()
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE_MB} MB.",
        )

    # Extract text
    try:
        if ext == ".pdf":
            raw_text = _extract_text_pdf(content)
            file_type = "PDF"
        else:
            raw_text = _extract_text_docx(content)
            file_type = "DOCX"
    except Exception as exc:
        # Log full detail server-side, return safe message to client
        import logging as _logging

        _logging.getLogger("cyberoracle").error(
            f"Document extraction failed for {filename}: {type(exc).__name__}: {exc}"
        )
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from this file. "
            "Ensure it is a valid, unprotected PDF or DOCX.",
        )

    if not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail=(
                "No text content found in this file. "
                "The document may be image-only or password-protected."
            ),
        )

    # DLP scan
    findings = _count_findings(raw_text)
    redacted_text, _ = scan_text(raw_text)
    total_redactions = sum(f.count for f in findings)

    # Audit log
    risk_score = min(1.0, total_redactions / 5.0) if total_redactions > 0 else 0.0
    severity = "high" if risk_score >= 0.7 else "medium" if risk_score >= 0.3 else "low"
    policy_decision = "redact" if total_redactions > 0 else "allow"
    finding_summary = ", ".join(f"{f.type}×{f.count}" for f in findings) or "none"

    await log_request(
        endpoint="/api/documents/sanitize",
        method="POST",
        status_code=200,
        message=(
            f"Document sanitized: {filename} ({file_type}), "
            f"redactions={total_redactions}, findings=[{finding_summary}]"
        ),
        event_type="document_sanitize",
        severity=severity,
        risk_score=risk_score,
        source="documents_route",
        policy_decision=policy_decision,
    )

    return SanitizeResponse(
        filename=filename,
        file_type=file_type,
        total_redactions=total_redactions,
        findings=findings,
        redacted_text=redacted_text,
    )
