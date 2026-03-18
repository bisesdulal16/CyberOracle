# CyberOracle — n8n Workflow Automation

## Overview

n8n automates the red-team alert → notification → log pipeline described in PSFR5.
It runs as a Docker container alongside the CyberOracle backend and polls the
`GET /api/alerts/recent` endpoint on a schedule, then routes high-severity
events to Slack and Discord.

---

## Quick start

### 1 — Add n8n to docker-compose

Append the following service to your `docker-compose.yml`:

```yaml
  n8n:
    image: n8nio/n8n:latest
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=changeme_n8n   # change this
      - WEBHOOK_URL=http://localhost:5678/
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  n8n_data:
```

Then run:
```bash
docker-compose up -d n8n
```

Open n8n at: **http://localhost:5678**

---

### 2 — Import the workflow

1. In the n8n UI, click **Workflows → Import from file**
2. Select `docs/n8n/cyberoracle-alert-workflow.json`
3. Click **Activate** to enable the schedule trigger

---

### 3 — Configure credentials

In n8n → Credentials, create:

| Name | Type | Value |
|------|------|-------|
| `CyberOracle API` | HTTP Header Auth | Header: `Authorization`, Value: `Bearer <admin-jwt>` |
| `Slack Webhook` | Slack Incoming Webhook | Your `SLACK_WEBHOOK_URL` |
| `Discord Webhook` | HTTP Request | Your `DISCORD_WEBHOOK_URL` |

---

## What the workflow does

```
Every 5 minutes
  ↓
GET /api/alerts/recent  (CyberOracle API)
  ↓
Filter: severity == "high"
  ↓
Any high alerts?
  ├── YES → Post to Slack + Discord with alert details
  └── NO  → Stop (no noise)
```

---

## Trigger: red-team webhook

CyberOracle can POST to n8n's webhook endpoint whenever a DLP block occurs.
Add this to `app/utils/alert_manager.py`:

```python
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")  # http://localhost:5678/webhook/cyberoracle

def notify_n8n(payload: dict):
    if N8N_WEBHOOK_URL:
        requests.post(N8N_WEBHOOK_URL, json=payload, timeout=3)
```

Then call `notify_n8n({"event": "dlp_block", "severity": "high", ...})` from the
DLP block path in `app/routes/ai.py`.

---

## Environment variables

Add to `.env`:

```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
N8N_WEBHOOK_URL=http://localhost:5678/webhook/cyberoracle
```
