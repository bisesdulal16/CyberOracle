# 🧩 CyberOracle — Week 5–6 Progress Report  
**Contributor:** Niall Chiweshe  
**Role:** Security / Auth / Testing / Exception Handling / Code Scanning  
**Period:** Nov 25 – Dec 6, 2025  

---

## 🎯 Objectives  
Strengthen backend reliability and secure coding posture by implementing centralized exception handling and integrating SonarQube static analysis to detect vulnerabilities and code-quality issues.

---

## 🧠 Tasks Completed  
| Task | Tool / Library | Status |
|------|----------------|--------|
| Implemented centralized exception-handling module | FastAPI | ✅ |
| Added secure fallback handlers (500, 404, ValidationError) | FastAPI | ✅ |
| Ensured error responses avoid leaking stack traces | OWASP ASVS | ✅ |
| Configured SonarQube service (running in Docker) | SonarQube LTS | ✅ |
| Generated code-quality + vulnerability reports | SonarScanner | ✅ |
| Created `sonar-project.properties` configuration | SonarScanner | ✅ |
| Integrated scanning workflow into local CI routine | CLI | ✅ |

---

## 📦 Deliverables  
| Deliverable | Description | File / Link |
|-------------|-------------|-------------|
| **Central Exception Handler** | Unified handler for ValidationError, HTTPException, Runtime errors | `app/utils/exception_handler.py` |
| **App Integration** | Middleware + custom exception inclusion | `app/main.py` |
| **SonarQube Config** | Project metadata + exclusions | `sonar-project.properties` |
| **SonarQube Scan Output** | Static analysis results + issues detected | See screenshots below |

---

## 🧪 Verification & Results  

| Check | Result | Screenshot |
|--------|--------|------------|
| Exception handler returns safe JSON response | ✅ Sanitized error output | <img width="1917" height="101" alt="image" src="https://github.com/user-attachments/assets/d06d7ffa-0103-48d9-9812-c4e01984bb7c" /> <img width="691" height="33" alt="image" src="https://github.com/user-attachments/assets/e5a8559d-6425-476f-ba7a-30a179d0c3ed" />|
| SonarQube container is running | ✅ `docker ps` shows active container | <img width="1916" height="139" alt="image" src="https://github.com/user-attachments/assets/0b64df18-e9a9-48a2-a707-3d456cb201c3" />|
| Local scan executed successfully | ✅ `sonar-scanner` completed without errors |  <img width="1239" height="82" alt="image" src="https://github.com/user-attachments/assets/e1edc2bc-623a-4c5e-86d6-78d22bb4281e" /><img width="1308" height="248" alt="image" src="https://github.com/user-attachments/assets/6bf667ff-f249-4f97-9914-3b0dde5e19db" />|
| Dashboard displays project results | ✅ Vulnerabilities + Code Smells visible | <img width="1919" height="945" alt="image" src="https://github.com/user-attachments/assets/0c27273b-2a13-473d-8592-8912fc2174c3" /> |

---

## 📊 Progress  
**Week 5–6 Progress Toward the Project:** **33%**  

| Requirement | Progress |
|--------------|----------|
| NCFR6 (Exception Handling) | ✅ Fully implemented |
| NCFR7 (DLP) | Completed in earlier week |
| NCFR8 (Security Tests) | Maintained |
| NCNR1 (Secure Code / PEP8 / OWASP) | Strengthened through SonarQube |

---

## 🔜 Next Steps  
- Enforce Quality Gate thresholds before merge  
- Add rule exceptions for false positives  
- Expand logging pipeline using Grafana dashboards  
- Prepare final presentation for CyberOracle security architecture  

---
