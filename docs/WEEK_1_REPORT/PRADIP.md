# CyberOracle — Week 1 Progress Report

**Contributor:** Pradip Sapkota  
**Role:** Security Engineer / Policy & Threat Modeling  
**Period:** Oct 28 – Nov 1, 2025  

---

## Objectives
Establish the security foundation for CyberOracle by defining the initial access-control model, data-loss-prevention (DLP) policy, and first-phase threat model.

---

## Tasks Completed

| Task | Area | Status |
|------|-------|---------|
| Designed RBAC model (Admin, Developer, Auditor) | RBAC / Policy | Completed |
| Defined regex-based DLP rules and severity levels | DLP Policy | Completed |
| Added alerting, rate-limiting, and compliance policies | Security Policy | Completed |
| Created STRIDE threat model for the API Gateway | Threat Modeling | Completed |
| Linked `policy.yaml` with threat model and Capstone II roadmap | Architecture | Completed |

---

## Deliverables

| Deliverable | Description | File |
|-------------|-------------|------|
| **policy.yaml (v1)** | Defines RBAC roles, DLP patterns, rate-limits, alert triggers, and compliance mappings | `policy.yaml` |
| **STRIDE Threat Model (v1)** | Documents security threats and mitigations for the API Gateway | `docs/threat-modeling/STRIDE-v1.md` |

---

## Key Highlights

### RBAC Design
Three initial roles defined:
- Admin — full operational and policy access  
- Developer — restricted access for testing and limited logs  
- Auditor — read-only access for compliance and monitoring  

---

### DLP Rule Set (v1)
Regex-based detection for:
- SSNs  
- Credit card numbers  
- API keys / tokens  
- Email addresses  

Each rule includes severity and description fields to support alerting and log workflows.

---

### Incident & Rate-Limit Policies
Defined:
- Role-based rate limits  
- Alerts for PII detection  
- Alerts for rate-limit violations  
- Alerts for authentication failures  
- Notification channels through Slack/Discord  

---

### STRIDE Threat Model
Threats mapped across:
- Spoofing  
- Tampering  
- Repudiation  
- Information disclosure  
- Denial of service  
- Elevation of privilege  

Each entry is linked to mitigation strategies referenced in `policy.yaml`.

---

## Verification & Review
- Validated structure and fields in `policy.yaml`  
- Ensured alignment with FERPA, SOC 2, GDPR, and HIPAA requirements  
- Reviewed threat-model linkages with RBAC and DLP rules  

---

## Overall Progress
Week 1 progress toward the overall project: **10%**

---

## Next Steps
- Implement regex-based DLP middleware  
- Build sample red-team prompt dataset  
- Begin unit tests for DLP and logging modules  

---
