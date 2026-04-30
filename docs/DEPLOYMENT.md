# CyberOracle — Deployment Guide

## Prerequisites

- Docker >= 24 and Docker Compose >= 2
- Python 3.10+
- Git
- `curl` and `jq` (for auth scripts)

---

## Quick Start (Docker Compose)

```bash
# 1. Clone the repository
git clone https://github.com/bisesdulal16/CyberOracle.git
cd CyberOracle

# 2. Copy and configure environment
cp .env.example .env        # edit credentials and keys before starting

# 3. Start the full stack (PostgreSQL + API + Grafana)
docker compose up -d

# 4. Verify all services are running
docker compose ps
```

API will be available at `http://localhost:8000`
Grafana at `http://localhost:3001`

---

## Manual Start (Development)

```bash
# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize DB tables and start API on port 8001
./start.sh
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL DSN — `postgresql+asyncpg://user:pass@host/db` |
| `JWT_SECRET_KEY` | Yes | HMAC-SHA256 signing secret (min 32 bytes in production) |
| `ADMIN_PASSWORD` | Yes | Admin user password |
| `DEV_PASSWORD` | Yes | Developer user password |
| `AUDITOR_PASSWORD` | Yes | Auditor user password |
| `DB_ENCRYPTION_ENABLED` | No | Set `true` to encrypt log messages at rest |
| `DB_ENCRYPTION_KEY` | If above is true | Fernet-compatible base64 key |
| `DB_ENCRYPTION_KEY_ID` | No | Key version label (default: `v1`) |
| `OLLAMA_MODEL` | No | LLM model name (default: `llama3.2:1b`) |
| `DISCORD_WEBHOOK_URL` | No | Discord webhook for DLP and anomaly alerts |

---

## Authentication

CyberOracle uses JWT (HS256, 30-minute expiry) with three roles:

| Role | Permissions | Rate Limit |
|---|---|---|
| `admin` | Full access — manage users, policies, all logs | 1000 req/min |
| `developer` | Query AI, view own logs, read DLP rules | 100 req/min |
| `auditor` | View all logs, generate compliance reports | 50 req/min |

### Obtain a token

```bash
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"changeme_admin"}' | jq -r '.access_token')

curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/auth/me
```

### Authenticate all roles at once

```bash
bash scripts/auth_all_roles.sh

# Export tokens as env vars
eval $(bash scripts/auth_all_roles.sh --export)
curl -H "Authorization: Bearer $TOKEN_ADMIN" http://localhost:8001/auth/me
curl -H "Authorization: Bearer $TOKEN_DEV"   http://localhost:8001/ai/query
```

---

## Scaling

### Docker Compose — scale to N replicas

```bash
bash scripts/scale_gateway.sh 3
```

### Kubernetes

```bash
kubectl apply -f infra/k8s/cyberoracle-deployment.yaml
kubectl apply -f infra/k8s/cyberoracle-service.yaml
kubectl apply -f infra/k8s/hpa.yaml          # auto-scales 2–10 replicas

# Manual scale
kubectl scale deployment/cyberoracle-api --replicas=5
```

---

## Key Rotation

Rotate the Fernet encryption key and re-encrypt all log records:

```bash
# Preview (no writes)
python scripts/key_rotation.py --dry-run

# Apply rotation — updates .env automatically
python scripts/key_rotation.py
```

---

## Running Tests

```bash
# Full suite with coverage (≥80% enforced)
pytest --cov=app --cov-fail-under=80 -q

# Single module
pytest tests/test_key_rotation.py -v
pytest tests/test_anomaly_alerting.py -v
```

---

## Monitoring

| Service | URL | Credentials |
|---|---|---|
| Grafana | http://localhost:3001 | admin / admin |
| Loki (log aggregation) | http://localhost:3100 | — |
| PostgreSQL | localhost:5434 | postgres / postgres |

---

## Security Scripts

| Script | Purpose |
|---|---|
| `scripts/auth_all_roles.sh` | Obtain JWT tokens for all three roles |
| `scripts/scale_gateway.sh` | Scale Docker Compose API replicas |
| `scripts/key_rotation.py` | Rotate Fernet encryption key |
| `scripts/anomaly_alerting.py` | Run anomaly detection and send Discord alerts |
| `scripts/run_prompt_injection_redteam.py` | Red-team prompt injection tests |
