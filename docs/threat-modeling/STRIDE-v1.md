# Cyberoracle Threat Modeling (STRIDE v1)

**Framework:** STRIDE  
**Author:** Pradip Sapkota  
**Date:** Week 1 Deliverable  

---

## System Context
Cyberoracle integrates a secure DevSecOps pipeline. The main assets and entry points we considered for Week 1 are:

- **Assets:** source code, CI/CD pipeline, build artifacts, secrets, database, logs, monitoring tools.  
- **Entry Points:** GitHub repo (push/PR), CI/CD runners, artifact repository, deployment scripts, application APIs, log/metrics collectors.

---

## STRIDE Threats (Draft v1)

| # | Threat | STRIDE Category | Risk (L/M/H) | Early Mitigation |
|---|--------|-----------------|--------------|------------------|
| 1 | Attacker pushes code by spoofing developer identity | **Spoofing** | High | Enforce MFA + SSO; signed commits; branch protection rules |
| 2 | Build artifacts tampered in CI/CD pipeline or storage | **Tampering** | High | Use artifact repository only; generate checksums + digital signatures |
| 3 | Risky changes with no audit trail (user denies action) | **Repudiation** | Medium | Enable log auditing for repo/CI; link commits to issue tracker |
| 4 | Secrets/tokens accidentally written to logs | **Information Disclosure** | High | Use `.env` + secret manager; log sanitization; developer training |
| 5 | Monitoring/alerting flood causes downtime | **Denial of Service** | Medium | Rate-limit noisy rules; auto-scaling; alert deduplication |
| 6 | Weak DB config → unauthorized admin access | **Elevation of Privilege** | High | DB encryption at rest + TLS; RBAC; isolation; DB audit tool |
| 7 | Dependency with known CVE pulled into build | **Tampering / Info Disclosure** | High | Run dependency/BOM checks; fail on criticals; pin versions |
| 8 | CI runner has excessive privileges, abused to reach prod | **Elevation of Privilege** | High | Least-privileged CI tokens; scoped cloud roles; signed artifacts |

---

## Notes
- This is **Draft v1** of our threat model.  
- We will refine it with data-flow diagrams and per-component analysis in Week 2–3.  
- Each mitigation should be opened as an **issue in GitHub** and tracked through the backlog → in-progress → done boards.  

---

**Deliverable complete:** This file satisfies Week 1 requirement for **Threat Modeling**.
