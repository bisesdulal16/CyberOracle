# CyberOracle
![CyberOracle CI](https://github.com/bisesdulal16/CyberOracle/actions/workflows/ci.yml/badge.svg)
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
- **Frontend** – React/Next.js dashboard for monitoring and interaction.  

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

## Threat Modeling
- [STRIDE v1 Threat Model](./threat-modeling/STRIDE-v1.md)
- [RBAC and DLP Policy Configuration](./threat-modeling/policy.yaml)

---

🟩 **Deployment Guide**
=======================

**1\. SSH Into the Server**
---------------------------

`   ssh STUDENTS\\bd0495@cyberoracle.eng.unt.edu   `

**2\. Navigate to the Project Directory**
-----------------------------------------

`   cd /opt/CyberOracle   `

**3\. Pull the Latest Changes From GitHub**
-------------------------------------------

Make sure no local changes exist. If unsure, reset safely:

`   git fetch --all  git reset --hard origin/main   `

Then pull:

`   git pull origin main   `

**4\. Rebuild the Docker Image**
--------------------------------

Every backend update requires a rebuild:

`   sudo docker build -t cyberoracle-api .   `

**5\. Restart the Docker Stack**
--------------------------------

This stops old containers and applies the new image:

`   sudo docker compose down  sudo docker compose up -d   `

**6\. Verify Containers Are Running**
-------------------------------------

`   sudo docker ps   `

Expected:

*   cyberoracle-api → running
    
*   cyberoracle-db → running
    
*   cyberoracle-grafana → running
    

**7\. Test the API Health**
---------------------------

`   curl http://localhost:8000/health   `

Expected output:

`   {"status": "ok", "message": "API healthy"}   `

**8\. (Optional) View Logs**
----------------------------

Backend logs:

`   sudo docker logs cyberoracle-api   `

Compose logs:

`   sudo docker compose logs -f   `

**9\. Running the UI**
--------------------------

To run the UI in development mode:

```bash
# Navigate to UI directory
cd ui/ui

# Install dependencies
npm install

# Start development server
npm run dev
```

The UI will be available at http://localhost:3000

## License
This project is licensed under the [MIT License](LICENSE).
