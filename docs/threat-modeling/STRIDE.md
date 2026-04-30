# CyberOracle Threat Model — STRIDE v2  
**Author:** Pradip Sapkota  
**Date:** March 2026  
**Scope:** CyberOracle Secure AI Gateway (FastAPI + DLP Engine + RBAC + Observability)  

---

## Objective
Define the security posture of CyberOracle by identifying threats across the AI gateway, DLP engine, authentication layer, document processing pipeline, and observability components. This model reflects the evolved system including advanced DLP (Presidio), alerting, dashboards, and red-team validation.

---

## System Overview
CyberOracle acts as a secure intermediary between users and AI models. It enforces security controls before and after model interaction.

### Core Components:
- FastAPI Gateway (API routing and validation)
- RBAC + JWT Authentication
- DLP Engine (Regex + Presidio + risk scoring)
- Document Sanitizer (PDF/DOCX ingestion)
- Logging & Audit System (Postgres)
- Alerts & Monitoring (alerts API + dashboard panels)
- Reports & Compliance Engine
- AI Model Adapter Layer (Ollama integration)

---

## Assets in Scope
| Category | Examples |
|----------|----------|
| Application | FastAPI routes, DLP engine, document processor |
| Data | Prompts, model outputs, uploaded documents, logs |
| Credentials | JWT tokens, API keys, environment secrets |
| Infrastructure | Docker services, Postgres DB |
| Monitoring | Alerts, audit logs, compliance reports |
| Users / Roles | Admin, Developer, Auditor (policy.yaml) |

---

## Trust Boundaries
1. **User → API Gateway** (external input boundary)
2. **Gateway → AI Model (Ollama)** (LLM interaction boundary)
3. **Gateway → Database** (log persistence boundary)
4. **Gateway → Document Processor** (file ingestion boundary)
5. **Backend → Frontend Dashboard** (data visualization boundary)

---

## STRIDE Threat Analysis

| STRIDE Category | Threat Example | Impact | Mitigation / Control |
|-----------------|----------------|--------|----------------------|
| **Spoofing** | Forged JWT tokens or impersonation | Unauthorized access | JWT authentication, role validation, RBAC enforcement |
| **Tampering** | Manipulated API payloads or document uploads | Data integrity loss | Input validation, file-type checks, DLP scanning |
| **Repudiation** | Users denying actions | Lack of accountability | Structured audit logging with timestamps |
| **Information Disclosure** | Exposure of PII (SSN, CC, API keys) in prompts or outputs | Data breach | Regex + Presidio DLP engine, redaction/blocking |
| **Denial of Service** | API flooding or large file uploads | Service degradation | Rate limiting middleware, file size limits |
| **Elevation of Privilege** | Unauthorized role escalation | Security compromise | RBAC enforcement via policy.yaml and backend checks |

---

## AI-Specific Threats

| Threat | Description | Mitigation |
|--------|------------|------------|
| Prompt Injection | Malicious prompts attempting to override system behavior | Input validation, DLP scanning, red-team testing |
| Data Exfiltration via LLM | Model leaking sensitive data in responses | Output DLP scanning and redaction |
| Model Abuse | Using AI endpoint for unintended operations | RBAC + request validation |
| Unsafe Output | Harmful or sensitive generated content | Output filtering + policy enforcement |

---

## Document Processing Threats

| Threat | Description | Mitigation |
|--------|------------|------------|
| Malicious File Upload | Unsupported or harmful files | File extension validation (.pdf, .docx only) |
| Hidden Sensitive Data | PII embedded in documents | DLP scanning and redaction |
| Empty / Corrupt Files | Extraction failures | Validation and error handling |

---

## Logging & Monitoring Threats

| Threat | Description | Mitigation |
|--------|------------|------------|
| Sensitive Data in Logs | Logs exposing PII | Masking/redaction + encryption support |
| Log Tampering | Unauthorized log modification | Controlled DB access + structured logging |
| Missed Security Events | No alert on suspicious activity | Alerts API + dashboard monitoring |

---

## Alerting & Observability

CyberOracle includes built-in observability:

- Alerts API (`/api/alerts/recent`)
- Metrics & Compliance APIs
- Dashboard panels (alerts, audit logs, reports)

### Risks:
- Delayed detection of threats  
- Alert fatigue  

### Controls:
- Severity classification (low/medium/high)
- Risk scoring via DLP engine
- Structured alert messages

---

## Security Controls Summary

| Control | Implementation |
|--------|---------------|
| Authentication | JWT-based login system |
| Authorization | RBAC via policy.yaml and backend enforcement |
| Data Protection | Regex + Presidio DLP engine |
| Input Validation | FastAPI validation + middleware |
| Logging | Structured logs stored in Postgres |
| Alerting | Alert manager + dashboard alerts |
| Testing | Automated tests + red-team dataset |
| Deployment | Docker-based environment |

---

## Linked Security Policy
See [`policy.yaml`](./policy.yaml) for:
- RBAC role definitions  
- DLP rules and severity levels  
- Rate-limiting policies  
- Alert thresholds  

---

## Notes for Future Enhancements
- Integration with external SIEM (Splunk / ELK / Grafana)
- OAuth2 / SSO authentication
- Advanced semantic firewall for prompt injection
- Automated red-team execution scheduling
- Infrastructure security with Terraform

---

**Version 2.0 — Updated for Capstone II (March 2026)**
