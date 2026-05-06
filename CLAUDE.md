# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CyberOracle is a secure AI gateway that acts as an intermediary between users and Ollama-hosted LLMs. It enforces security controls (DLP, RBAC, rate limiting) before and after every model interaction.

## Commands

### Development Setup
```bash
pip install -r requirements.txt
pre-commit install   # enables gitleaks secret scanning on commits
```

### Run Tests
```bash
# Full suite — 80% coverage is enforced
pytest --cov=app --cov-fail-under=80 --maxfail=1 --disable-warnings -q

# Single test file
pytest tests/test_app.py -v

# Single test function
pytest tests/test_app.py::test_health_endpoint -v

# Pattern match
pytest -k "dlp" -v
```

### Linting & Formatting
```bash
black --check .    # check only
black .            # format in place
flake8 .
```

### Start the Application
```bash
docker compose up -d          # full stack (PostgreSQL on 5434, API on 8000, Grafana on 3001)
./start.sh                    # manual: initializes DB tables, starts uvicorn on port 8001 with reload
```

## Architecture

### Request Flow
Every AI query follows this pipeline:
1. **Rate Limiter** middleware (per-IP, per-role sliding window, 60s)
2. **DLP Filter** middleware scans the request
3. **RBAC** check via JWT (`require_permission("test_api_endpoints")`)
4. **DLP Engine** (`app/services/dlp_engine.py`) — dual-layer scan (regex + Presidio), returns `DlpDecision` (allow/redact/block) and risk score 0.0–1.0
5. **Model Router** (`app/services/model_router.py`) → **Ollama Client** (`app/services/ollama_client.py`) — dispatches to Ollama (default model: `llama3.2:1b`)
6. Output DLP scan before response is returned
7. Audit log written to PostgreSQL (`LogEntry` model)

### Key Layers

**Routes** (`app/routes/`): thin HTTP handlers — `ai.py`, `auth.py`, `dlp.py`, `documents.py`, `logs.py`, `metrics.py`, `reports.py`.

**Services** (`app/services/`): business logic — `dlp_engine.py` (central DLP), `model_router.py`, `ollama_client.py`, `compliance_engine.py`, `threat_detector.py`, `circuit_breaker.py`.

**Middleware** (`app/middleware/`): `dlp_filter.py`, `rate_limiter.py`, `dlp_regex.py` (pattern library), `dlp_presidio.py` (Microsoft Presidio wrapper), `api_key_auth.py`.

**Auth** (`app/auth/`): `rbac.py` (FastAPI dependencies `require_roles()` / `require_permission()`), `jwt_utils.py`, `policy_loader.py` (reads `docs/threat-modeling/policy.yaml`), `permissions.py`.

**Utilities** (`app/utils/`): `logger.py` (masks PII in logs), `db_encryption.py` (Fernet), `alert_manager.py` (Discord/Slack/email), `exception_handler.py` (masks internal errors in responses).

### Database
- PostgreSQL via SQLAlchemy async + asyncpg.
- Two ORM models in `app/models.py`: `User` and `LogEntry`.
- Optional per-record Fernet encryption controlled by `DB_ENCRYPTION_ENABLED` env var.

### Policy Configuration
`docs/threat-modeling/policy.yaml` is the single source of truth for RBAC roles (admin/developer/auditor), per-role rate limits, DLP regex rules, and compliance frameworks (GDPR, HIPAA, FERPA, SOC2). `app/auth/policy_loader.py` reads this at startup.

## Test Organization

Tests live in two trees that mirror each other:
- `/tests/` — primary unit and integration tests
- `/app/tests/` — additional integration tests (loaded by the same pytest run)

`conftest.py` resets the rate limiter state before/after each test and sets `PYTEST=1` to disable certain side effects.

## CI/CD

Three GitHub Actions pipelines run on push/PR to `main`:
- **`ci.yml`**: lint → test (≥80% coverage) → Kubernetes manifest validation (with a PostgreSQL 16 service container)
- **`codeql.yml`**: CodeQL static analysis (Python, JS/TS)
- **`secret-scan.yml`**: TruffleHog `--only-verified` secret scanning

## Key Environment Variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL DSN (required) |
| `JWT_SECRET_KEY` | JWT signing secret |
| `OLLAMA_MODEL` | Model name sent to Ollama (default: `llama3.2:1b`) |
| `DB_ENCRYPTION_ENABLED` / `DB_ENCRYPTION_KEY` | Toggle and key for log encryption |
| `ADMIN_PASSWORD`, `DEV_PASSWORD`, `AUDITOR_PASSWORD` | Seed credentials |
| `DISCORD_WEBHOOK_URL`, `SLACK_WEBHOOK_URL` | Optional alert targets |
| `PYTEST` | Set to `1` inside tests to suppress side effects |
