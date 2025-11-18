
---

# CyberOracle — Week 2 Progress Report
**Contributor:** Niall Chiweshe  
**Role:** Security / Authentication / Validation  
**Period:** Nov 4 – Nov 8, 2025  

---

## 🎯 Objectives
Expand the backend security layer by implementing rate-limiting, sanitization, and validation utilities, and writing early automated tests to confirm expected behavior.

---

## 🧠 Tasks Completed
| Task | Tool / Library | Status |
|------|-----------------|--------|
| Implemented IP-based rate-limiting middleware | FastAPI, Starlette | ✅ |
| Added request sanitization & validation utilities | Python, Regex | ✅ |
| Created initial unit tests for rate-limiting and validation | Pytest, HTTPX | ✅ |
| Configured PYTEST environment flag for deterministic throttling | dotenv | ✅ |
| Ensured middleware executes in correct order for all routes | FastAPI | ✅ |

---

## 📦 Deliverables
| Deliverable | Description | File / Link |
|--------------|-------------|--------------|
| **Rate Limiter** | Enforces request limits per IP to mitigate brute-force & DoS attacks | `app/middleware/rate_limiter.py` |
| **Input Validation Layer** | Sanitization helpers and safe-input rules | `app/utils/validation.py` |
| **Unit Tests** | Automated tests confirming behavior | `app/tests/middleware/test_rate_limit.py`, `app/tests/utils/test_validation.py` |
| **Environment Configuration** | PYTEST flag mapped to test-mode behavior | `.env` |

---

## 🧪 Verification & Results
| Check | Result | Screenshot |
|--------|---------|------------|
| Rate-limiter blocks the 6th request | ✅ Confirmed via pytest | <img width="1919" height="709" alt="image" src="https://github.com/user-attachments/assets/fc4d8b2f-f0c3-4eef-b889-9c2bc3b8c083" /> |
| Validation layer rejects unsafe patterns | ✅ Tests passing | <img width="1919" height="87" alt="image" src="https://github.com/user-attachments/assets/78ecccce-2150-41e9-ba97-d079efe81ee6" /> |
| PYTEST flag correctly activates test-mode throttling | ✅ Verified in REPL | <img width="1044" height="209" alt="image" src="https://github.com/user-attachments/assets/a9904bfe-5111-4978-9342-aceca972c557" /> |

---

## 📊 Progress
**Week 2 Progress toward the Project:** **17%**  

| Requirement | Progress |
|------------|----------|
| NCFR1 (Rate Limiting) | ✅ Fully implemented |
| NCFR2 (Authentication) | Baseline utilities exist from Week 1 |
| NCFR3 (Input Validation) | ✅ Rules and helpers added |
| NCFR4 (TLS/HTTPS) | Not started |
| NCFR5 (Secure Logging / Masking) | Not started |
| NCFR6 (Safe Error Handling) | Not started |
| NCFR7 (DLP Scanning) | Not started |
| NCFR8 (Security Tests) | ✅ Initial tests completed |
| NCNR1 (PEP8/OWASP Documentation) | Maintained through comments and linting |

---

## 🔜 Next Steps
- Configure HTTPS/TLS for local development  
- Implement secure masked logging for sensitive input  
- Add additional unit tests for full security coverage  
- Integrate tests with CI and enforce coverage thresholds  

---
