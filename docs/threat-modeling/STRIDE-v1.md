# CyberOracle Threat Model — STRIDE v1  
**Author:** Pradip Sapkota  
**Date:** October 28, 2025  
**Scope:** CyberOracle API Gateway (FastAPI + DLP + RBAC)  

---

## Objective
Define the first-phase security posture for CyberOracle by identifying threats to the AI gateway, data-loss-prevention pipeline, and compliance modules.

---

## Assets in Scope
| Category | Examples |
|-----------|-----------|
| Application | FastAPI gateway, DLP middleware, Presidio integration |
| Data | API payloads, logs, credentials, user metadata |
| Infrastructure | Dockerized containers, Postgres database, TLS certificates |
| Users / Roles | Admin, Developer, Auditor (defined in [policy.yaml](./policy.yaml)) |

---

## STRIDE Threat Analysis

| STRIDE Category | Threat Example | Mitigation / Control |
|-----------------|----------------|----------------------|
| **Spoofing** | Forged API tokens or fake user identities | JWT authentication and RBAC policy enforcement |
| **Tampering** | Payload modification in transit | TLS 1.3 and DLP middleware redaction of sensitive content |
| **Repudiation** | Users denying actions | Audit logs stored in Postgres with retention policies |
| **Information Disclosure** | Exposure of SSNs, credit cards, or API keys | Regex and Presidio-based DLP detection and blocking |
| **Denial of Service** | Excessive API calls or rate abuse | Role-based rate limits (see policy.yaml → rate_limiting) |
| **Elevation of Privilege** | Developer gaining admin access | Enforced RBAC roles (Admin/Dev/Auditor) with restricted permissions |

---

## Linked Security Policy
See [`policy.yaml`](./policy.yaml) for:
- RBAC role definitions  
- DLP patterns and severity levels  
- Rate-limiting controls  
- Alert triggers and compliance frameworks  

---

## Notes for Capstone II
In Capstone II this threat model will expand to include:
- OAuth2/JWT authorization flows  
- Terraform infrastructure-as-code and cloud security mapping  
- Automated red-team attack simulation using n8n workflows  

---

**Version 1.0 — Reviewed and committed October 2025.**
