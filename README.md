# CyberOracle

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)]()
[![Security](https://img.shields.io/badge/security-scanned-success.svg)]()

**CyberOracle** is a secure AI gateway and compliance automation platform designed to protect Large Language Model (LLM) workflows.  
It enforces data security, compliance checks, and observability while enabling safe enterprise adoption of AI.  

---

## Overview
CyberOracle provides:
- **Gateway** – FastAPI-based service running inside Docker with TLS-enabled reverse proxy.  
- **Data Security** – Regex-based DLP (Data Loss Prevention), with planned integration of Microsoft Presidio and TruffleHog.  
- **Compliance** – Policy checks (RBAC, red-team automation, continuous scanning).  
- **Observability** – PostgreSQL logging with Grafana dashboards, Prometheus, and Loki.  

---

## Features

### Current (MVP – Semester 1)
- Infrastructure setup with Docker + FastAPI + TLS  
- Logging to PostgreSQL  
- Regex-based DLP scanning  
- Baseline security scans (Trivy, Bandit)  
- Basic observability with Grafana  

### Planned (Scaling – Semester 2)
- Advanced DLP (Presidio, TruffleHog)  
- Prompt Injection Firewall  
- RBAC Enforcement  
- Automated red-team testing with n8n  
- Continuous monitoring (Prometheus, Loki, Jaeger)  

---

## Tech Stack
- **FastAPI** – API gateway framework  
- **Docker & Traefik** – Containerization and TLS reverse proxy  
- **PostgreSQL** – Logging database  
- **Grafana & Prometheus** – Monitoring and visualization  
- **Trivy & Bandit** – Security scanning tools  

---

## Getting Started

### Prerequisites
- Docker & Docker Compose  
- Python 3.10+  
- Git  

## Access
- API Gateway: https://localhost:8000  
- Grafana Dashboard: http://localhost:3000  

---

## Issue Tracking
We use [GitHub Issues](https://github.com/your-org/cyberoracle/issues) with the following labels:  
- **bug** – Problems or errors  
- **feature** – New functionality  
- **security** – Security-related tasks  
- **documentation** – Documentation tasks  

---

## Documentation
- [`/docs`](./docs) – Setup guides, architecture diagrams, and compliance checklists  

---

## License
This project is licensed under the [MIT License](LICENSE).
