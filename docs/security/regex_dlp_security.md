# CyberOracle — Regex DLP Security Justification

**Author:** Pradip Sapkota  
**Component:** PSFR2 — Secure FastAPI Middleware  
**Date:** November 2025

---

## 1. Purpose of the Regex DLP Module

The regex-based Data Loss Prevention (DLP) module provides the first layer of protection against accidental or malicious exposure of sensitive information inside API payloads. This ensures that high-risk data such as SSNs, credit card numbers, email addresses, and API keys are detected and sanitized *before* they reach logs, database storage, monitoring pipelines, or downstream AI systems.

This module helps prevent data leakage, compliance violations, and insecure logging — all of which represent top OWASP and NIST data security risks.

---

## 2. Threats Mitigated

| Threat | Description | Mitigation via Regex DLP |
|--------|-------------|---------------------------|
| **PII leakage through logs** | Sensitive data can be logged by API handlers or frameworks | Regex engine scans and redacts PII before request reaches application |
| **Exposure of API keys / secrets** | Credentials may be accidentally submitted through form fields or API calls | API key pattern detection prevents storage or forwarding of secrets |
| **Accidental developer misuse** | Developers testing endpoints sometimes send live PII | Middleware sanitizes payloads automatically |
| **Prompt injection via sensitive data** | Attackers embed PII inside LLM prompts to cause downstream exposure | Regex DLP blocks or redacts before prompt enters LLM pipeline |
| **Compliance violations (GDPR, HIPAA, FERPA)** | Organizations must avoid storing personal identifiers | Redaction ensures nothing sensitive is persisted |

---

## 3. How the Regex Engine Works

The module defines a structured dictionary of regex patterns:
```python
SENSITIVE_PATTERNS = {
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "api_key": r"\b[A-Za-z0-9]{32,}\b"
}
```

### Execution Workflow

1. Incoming POST/PUT/PATCH requests are intercepted by FastAPI middleware.
2. The JSON body is parsed safely.
3. For each string field:
   - Regex patterns are applied one-by-one.
   - Matches are replaced with placeholders (`<SSN>`, `<CREDIT_CARD>`, etc.).
4. The sanitized payload replaces the original request body.
5. Downstream routes and loggers only receive redacted data.

This design ensures that no sensitive substring ever exits the middleware unprotected.

---

## 4. Security Guarantees

✔ **Zero sensitive data written to logs**  
Middleware completes sanitization before application logging or DB insertion.

✔ **Deterministic redaction**  
If a pattern matches, it is always replaced — no probabilistic behavior.

✔ **Lightweight and fast**  
Regex scanning operates in constant time relative to payload size and requires no external NLP models.

✔ **Consistent with industry compliance**  
Matches requirements from:
- NIST SP 800-53 (AU-9, SC-28)
- GDPR Article 32
- HIPAA Technical Safeguards

---

## 5. Current Limitations

Regex-only DLP is intentionally simple but has known limitations:

| Limitation | Impact | Mitigation Plan |
|------------|--------|-----------------|
| Format-based detection only | Cannot catch context-dependent PII | Addressed in Week 3 using Presidio NLP models |
| No detection of obfuscated PII | Attackers can evade by spacing or encoding | Covered in DLP v2 merge (Week 5–6) |
| No detection inside nested objects | Only top-level fields are scanned | Planned improvement: recursive JSON scanner |

These limitations are documented to show clear upgrade paths in Capstone II.

---

## 6. Conclusion

The regex-based DLP module fulfills PSFR2 by providing:

- A secure middleware layer
- Reliable pattern-based detection
- Redaction before logs/DB application code
- Clear compliance and security benefits