# CyberOracle — Week 3 Progress Report
**Contributor:** Niall Chiweshe  
**Role:** Security / TLS / Logging  
**Period:** Nov 11 – Nov 15, 2025  

---

## 🎯 Objectives
Implement secure HTTPS for local development and integrate masked logging to ensure sensitive data is not exposed in logs or database entries.

---

## 🧠 Tasks Completed
| Task | Tool / Library | Status |
|------|-----------------|--------|
| Generated local TLS certificates for HTTPS | OpenSSL | ✅ |
| Added HTTPS launch script (`run_https.sh`) | Uvicorn | ✅ |
| Configured FastAPI app to load TLS certs | FastAPI, Uvicorn | ✅ |
| Added secure logging with masking for sensitive fields | Python logging, regex | ✅ |
| Added async DB log ingestion via `/logs/ingest` | SQLAlchemy | ✅ |
| Verified secure logging does not store plaintext secrets | Manual + pytest | ✅ |

---

## 📦 Deliverables
| Deliverable | Description | File / Link |
|--------------|-------------|--------------|
| **TLS Certificates** | Self-signed cert + private key for local HTTPS | `certs/server.crt`, `certs/server.key` |
| **HTTPS Runner Script** | Starts backend on `https://localhost:8443` | `scripts/run_https.sh` |
| **Secure Logging Module** | Masking for passwords, tokens, API keys | `app/utils/logger.py` |
| **Logs Endpoint** | Accepts log records & stores them masked | `app/routes/logs.py` |
| **Database Logging Model** | Structured log storage | `app/models.py` |

---

## 🧪 Verification & Results
| Check | Result | Screenshot |
|--------|---------|------------|
| HTTPS server starts successfully | ✅ `curl -k https://localhost:8443/health` returns JSON | <img width="1525" height="787" alt="image" src="https://github.com/user-attachments/assets/86c2e792-3b74-4a59-8584-cbe4f1466909" /> <img width="1519" height="85" alt="image" src="https://github.com/user-attachments/assets/61bdf0fb-95f1-4527-af05-1951dd7b283c" />|
| Cert/key files recognized by Uvicorn | ✅ Verified via terminal output | <img width="1306" height="711" alt="image" src="https://github.com/user-attachments/assets/adca0c5b-6781-4617-ba59-179e87528779" />|
| Masked logging hides sensitive fields | ✅ Password/API key replaced with `***MASKED***` | <img width="1919" height="91" alt="image" src="https://github.com/user-attachments/assets/3704e0a1-2094-4a63-89b0-0ff9f14bed38" /> <img width="1919" height="116" alt="image" src="https://github.com/user-attachments/assets/9d8d6b12-2497-4ec6-84f5-3c644e9e7c5c" /> |
| Log ingestion writes masked values to DB | ✅ Verified in SQL query | <img width="1919" height="594" alt="image" src="https://github.com/user-attachments/assets/2311d33c-0cc2-4d7a-9c0d-bf7c1245874e" /> |

---

## 📊 Progress
**Week 3 Progress toward the Project:** **22%**

| Requirement | Progress |
|------------|----------|
| NCFR4 (TLS/HTTPS) | ✅ Completed |
| NCFR5 (Secure Logging / Masking) | ✅ Completed |
| NCFR2 (Authentication) | Completed Week 1 |
| NCFR1 (Rate Limiting) | Completed Week 2 |
| NCFR3 (Validation) | Completed Week 2 |
| NCFR7 (DLP Scanning) | Not started |
| NCFR8 (Security Tests) | In progress |
| NCNR1 (PEP8/OWASP Documentation) | Maintained across modules |

---

## 🔜 Next Steps
- Extend masked logging to capture request metadata  
- Add exception-safe error middleware  
- Implement DLP scanning engine (regex + Presidio hybrid)  
- Increase unit test coverage to >80%  

---
