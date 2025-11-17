# 🧩 CyberOracle — Week 1 Progress Report
**Contributor:** Niall Chiweshe  
**Role:** Security / Authentication / Validation  
**Period:** Oct 28 – Nov 1, 2025  

---

## 🎯 Objectives
Establish project security foundations by setting up authentication scaffolding, input validation utilities, and repository linting/formatting enforcement.

---

## 🧠 Tasks Completed
| Task | Tool / Library | Status |
|------|-----------------|--------|
| Set up local development environment and cloned repo | Git, Python venv | ✅ |
| Installed full backend dependencies | pip, requirements.txt | ✅ |
| Added initial JWT & API key authentication utilities | python-jose, FastAPI | ✅ |
| Added basic input validation layer | Pydantic | ✅ |
| Configured project-wide linting (flake8 + black) | flake8, black | ✅ |
| Verified project structure and ensured OWASP-aligned file layout | Code review | ✅ |

---

## 📦 Deliverables
| Deliverable | Description | File / Link |
|--------------|-------------|--------------|
| **JWT Utilities** | Token creation & verification logic | `app/auth/jwt_utils.py` |
| **API Key Handler** | Basic API key validation | `app/auth/api_key_utils.py` |
| **Input Validation Layer** | Sanitization & validation helpers | `app/utils/validation.py` |
| **Formatting & Linting System** | Black + flake8 configuration | `.flake8` |
| **Environment Template** | Secure environment variable structure | `.env.example` |

---

## 🧪 Verification & Results
| Check | Result | Screenshot |
|--------|---------|------------|
| Black Formatting (`black --check .`) | ✅ `All done! ✨ 🍰 ✨` | <img width="695" height="60" alt="image" src="https://github.com/user-attachments/assets/a6e8f713-a60f-4bf7-a091-4ff57308cb78" />|
| flake8 Validation | ✅ No violations reported |<img width="640" height="43" alt="image" src="https://github.com/user-attachments/assets/0fdb80f7-adfe-4383-a408-138a8ccfd27f" />|
| Authentication modules imported successfully | ✅ Verified in Python REPL | <img width="1176" height="313" alt="image" src="https://github.com/user-attachments/assets/c71d5c05-110d-4ff5-b184-ffd79819599c" />|
| Repo structure follows security best practices | ✅ OWASP/PEP8-aligned layout | <img width="898" height="673" alt="image" src="https://github.com/user-attachments/assets/adf1000b-64a5-45af-8564-3c2984255a4d" /> <img width="736" height="595" alt="image" src="https://github.com/user-attachments/assets/0540cc73-e139-4bf1-8e9a-bd78a00909de" /> <img width="762" height="718" alt="image" src="https://github.com/user-attachments/assets/8dc75d55-c95e-49c7-96da-98d5766c8662" />|

---

## 📊 Progress
**Week 1 Progress towards the Project:** **10%**

| Requirement | Progress |
|------------|----------|
| NCFR1 (Rate Limiting) | Not started |
| NCFR2 (Authentication) | 🔹 Initial utilities completed |
| NCFR3 (Input Validation) | 🔹 Baseline functions added |
| NCFR4 (TLS/HTTPS) | Not started |
| NCFR5 (Secure Logging / Masking) | Not started |
| NCFR6 (Safe Error Handling) | Not started |
| NCFR7 (DLP Scanning) | Not started |
| NCFR8 (Security Tests) | Not started |
| NCNR1 (PEP8/OWASP Documentation) | 🔹 Achieved through linting + comments |

---

## 🔜 Next Steps
- Begin development of DLP (regex + Presidio) scanning middleware  
- Expand JWT authentication into full RBAC model  
- Add tests for authentication, validation, and rate-limiting  
- Integrate coverage >80% into CI pipeline  

---
