# CyberOracle — Week 4 Progress Report
**Contributor:** Niall Chiweshe  
**Role:** Security / Testing / CI Integration  
**Period:** Nov 18 – Nov 22, 2025  

---

## 🎯 Objectives
Expand automated test coverage for security-critical modules (authentication and rate-limiting), verify correctness through pytest, and ensure test execution is fully integrated into the CI pipeline.

---

## 🧠 Tasks Completed
| Task | Tool / Library | Status |
|------|-----------------|--------|
| Verified authentication module behavior (JWT + API keys) | python-jose, secrets | ✅ |
| Verified rate-limiting logic through automated pytest suite | Pytest, HTTPX | ✅ |
| Integrated authentication + rate-limit tests into CI pipeline | GitHub Actions | ✅ |
| Ensured coverage threshold (80 percent) enforced in CI | Coverage.py | ✅ |
| Confirmed all Week 1–3 tests run in sequence without conflicts | Pytest | ✅ |

---

## 📦 Deliverables
| Deliverable | Description | File / Link |
|-------------|-------------|--------------|
| **Authentication Tests** | Validates JWT creation/verification and API key handling | `app/tests/auth/test_jwt.py`, `app/tests/auth/test_api_key.py` |
| **Rate-Limit Tests** | Validates 5 allowed requests + 6th blocked with HTTP 429 | `app/tests/middleware/test_rate_limit.py`, `app/tests/middleware/test_rate_limit_extra.py` |
| **Full CI Test Integration** | Tests auto-run on pull requests | `.github/workflows/ci.yml` |
| **Coverage Enforcement** | CI fails if coverage < 80 percent | CI step: `pytest --cov=app --cov-fail-under=80` |

---

## 🧪 Verification & Results
| Check | Result | Screenshot |
|--------|---------|------------|
| Authentication tests passing | ✅ JWT + API key tests validated | <img width="1919" height="95" alt="image" src="https://github.com/user-attachments/assets/80c3a254-af31-4001-a6ee-36596d6ae932" />|
| Rate-limiting tests passing | ✅ 6th request blocked as expected | <img width="1919" height="738" alt="image" src="https://github.com/user-attachments/assets/bb11dd47-4c93-4467-a04d-a8b1d5de16f1" />|
| All tests passing together | ✅ Pytest run succeeds locally | <img width="1919" height="776" alt="image" src="https://github.com/user-attachments/assets/2e8de274-43fe-4503-bbde-6be259413d5a" /> |
| CI Pipeline test stage | ✅ CI triggered on PR and passed | <img width="1489" height="86" alt="image" src="https://github.com/user-attachments/assets/9c620b08-59c2-4450-a99c-be24497d7436" /> <img width="1483" height="87" alt="image" src="https://github.com/user-attachments/assets/7989a1ab-6cae-46f5-b372-a5040a2e126c" /> <img width="1430" height="90" alt="image" src="https://github.com/user-attachments/assets/de2b701e-2228-4c26-b77b-a5a18e7dc871" /> |
| Coverage ≥ 80 percent | ✅ Verified through coverage report | <img width="1477" height="743" alt="image" src="https://github.com/user-attachments/assets/48ec26ab-90dc-4c48-9848-25c835591734" /> <img width="1381" height="723" alt="image" src="https://github.com/user-attachments/assets/3d05855f-98ac-4d03-9603-bd586ab75ac9" />|


---

## 📊 Progress
**Week 4 Progress toward the Project:** **27 percent**

| Requirement | Progress |
|------------|----------|
| NCFR1 (Rate Limiting) | Fully validated through tests |
| NCFR2 (Authentication) | Verified via JWT + API key tests |
| NCFR3 (Input Validation) | Covered by Week 2 tests |
| NCFR4 (TLS/HTTPS) | Completed in Week 3 |
| NCFR5 (Secure Logging / Masking) | Verified by ingest + DB inspection |
| NCFR6 (Safe Error Handling) | Partial (no leakage in tests) |
| NCFR7 (DLP Scanning) | Covered in Week 3 |
| NCFR8 (Security Tests) | Fully integrated with CI |
| NCNR1 (Documentation + Code Quality) | Maintained through linting + comments |

---

## 🔜 Next Steps
- Begin development of RBAC enhancements for auth system  
- Expand DLP scanning tests to integrate regex + Presidio  
- Add HTTPS certificate validation tests  
- Strengthen database logging assertions  

---
