# CyberOracle

![CyberOracle CI](https://github.com/bisesdulal16/CyberOracle/actions/workflows/ci.yml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)]()
[![Security](https://img.shields.io/badge/security-scanned-success.svg)]()
[![Release](https://img.shields.io/badge/release-v1.0.0-blue.svg)](https://github.com/bisesdulal16/CyberOracle/releases/tag/v1.0.0)

CyberOracle is a secure AI gateway that sits between users and Ollama-hosted LLMs. Every request is scanned for sensitive data, checked against role-based access policies, logged with tamper-evident hashes, and monitored in real time — before and after the model responds.

---

## What It Does

- **DLP** — Detects and redacts PII/PHI (SSN, credit cards, API keys, emails, and 25+ more) using regex and Microsoft Presidio
- **RBAC** — JWT-based access control with three roles: admin, developer, auditor
- **Rate Limiting** — Per-IP, per-role sliding window enforced on every endpoint
- **Encryption** — Fernet encryption on all log records + pgcrypto at the database level
- **Anomaly Detection** — Flags unusual request rates, large payloads, high-risk DLP events, and repeated blocks
- **Alerting** — Real-time Discord notifications on DLP violations and anomalies
- **Audit Logging** — Every request written to PostgreSQL with SHA-256 integrity hash
- **Grafana Dashboards** — DLP metrics, compliance panels (FERPA, HIPAA, NIST CSF), log analysis
- **Scaling** — Docker Compose replica scaling + Kubernetes HPA (2–10 replicas)

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Gateway | FastAPI + Uvicorn |
| AI Backend | Ollama (llama3.2:1b) |
| DLP | Regex + Microsoft Presidio |
| Auth | JWT HS256 + bcrypt |
| Database | PostgreSQL 16 + SQLAlchemy async |
| Encryption | Fernet (app-level) + pgcrypto (DB-level) |
| Monitoring | Grafana + Loki + Promtail |
| Containers | Docker + Docker Compose |
| Orchestration | Kubernetes + HPA |
| Infrastructure | Terraform |
| CI/CD | GitHub Actions |

---

## Prerequisites

- Docker >= 24 and Docker Compose >= 2
- Python 3.10+
- Git
- `curl` and `jq`

---

## Installation

### Option 1 — Docker Compose (Recommended)

```bash
git clone https://github.com/bisesdulal16/CyberOracle.git
cd CyberOracle

cp .env.example .env
# Edit .env — set JWT_SECRET_KEY, ADMIN_PASSWORD, DEV_PASSWORD, AUDITOR_PASSWORD

docker compose up -d
docker compose ps
```

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Grafana | http://localhost:3001 |
| PostgreSQL | localhost:5434 |

### Option 2 — Manual

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pre-commit install
./start.sh          # initializes DB and starts API on port 8001
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL DSN |
| `JWT_SECRET_KEY` | Yes | Signing secret — minimum 32 bytes in production |
| `ADMIN_PASSWORD` | Yes | Admin user password |
| `DEV_PASSWORD` | Yes | Developer user password |
| `AUDITOR_PASSWORD` | Yes | Auditor user password |
| `DB_ENCRYPTION_ENABLED` | No | Set `true` to encrypt log messages at rest |
| `DB_ENCRYPTION_KEY` | If above true | Fernet base64 key |
| `DB_ENCRYPTION_KEY_ID` | No | Key version (default: `v1`) |
| `OLLAMA_MODEL` | No | Model name (default: `llama3.2:1b`) |
| `DISCORD_WEBHOOK_URL` | No | Webhook for DLP and anomaly alerts |

---

## Authentication

```bash
# Get a token
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"changeme_admin"}' | jq -r '.access_token')

curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/auth/me

# Authenticate all three roles at once
bash scripts/auth_all_roles.sh

# Export tokens as shell variables
eval $(bash scripts/auth_all_roles.sh --export)
```

| Role | Permissions | Rate Limit |
|---|---|---|
| `admin` | Full access | 1000 req/min |
| `developer` | AI queries, own logs, DLP rules | 100 req/min |
| `auditor` | View all logs, compliance reports | 50 req/min |

---

## TLS Setup

```bash
# Self-signed (development)
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -keyout certs/server.key -out certs/server.crt \
  -days 365 -nodes -subj "/CN=localhost"
bash scripts/run_https.sh

# Verify
curl -k https://localhost:8443/health
```

For Let's Encrypt production setup see [docs/TLS_SETUP.md](docs/TLS_SETUP.md).

---

## Deployment (Production Server)

```bash
ssh STUDENTS\bd0495@cyberoracle.eng.unt.edu
cd /opt/CyberOracle

git fetch --all && git reset --hard origin/main && git pull origin main

sudo docker build -t cyberoracle-api .
sudo docker compose down
sudo docker compose up -d

sudo docker compose ps
curl http://localhost:8000/health
```

---

## Scaling

```bash
# Docker Compose
bash scripts/scale_gateway.sh 3

# Kubernetes
kubectl apply -f infra/k8s/cyberoracle-deployment.yaml
kubectl apply -f infra/k8s/cyberoracle-service.yaml
kubectl apply -f infra/k8s/hpa.yaml
```

---

## Security Scripts

```bash
# Key rotation (re-encrypts all DB records, updates .env)
python scripts/key_rotation.py --dry-run   # preview
python scripts/key_rotation.py             # apply

# Anomaly detection + Discord alerts
python scripts/anomaly_alerting.py

# Prompt injection red-team tests
python scripts/run_prompt_injection_redteam.py
```

---

## Testing

```bash
pytest --cov=app --cov-fail-under=80 -q
```

---

## Documentation

| Document | Description |
|---|---|
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Full deployment guide |
| [docs/TLS_SETUP.md](docs/TLS_SETUP.md) | TLS/HTTPS configuration |
| [docs/threat-modeling/STRIDE.md](docs/threat-modeling/STRIDE.md) | STRIDE threat model |
| [docs/threat-modeling/policy.yaml](docs/threat-modeling/policy.yaml) | RBAC roles, rate limits, DLP rules |

---

## Release

Latest: [v1.0.0](https://github.com/bisesdulal16/CyberOracle/releases/tag/v1.0.0)

Includes Dockerfile, docker-compose.yml, Kubernetes manifests, Terraform configs, deployment guide, TLS setup guide, and all security scripts.

```bash
# Package a release locally
bash scripts/package_release.sh v1.0.0
```

---

## License

[MIT](LICENSE)
