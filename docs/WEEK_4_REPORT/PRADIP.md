# CyberOracle — Week 4 Progress Report

**Contributor:** Pradip Sapkota  
**Role:** Alerting System / Security Engineering / Notifications  
**Period:** Nov 18 – Nov 22, 2025  

---

## Objectives
Implement real-time security alerting for CyberOracle, including payload anomaly alerts, rate-limit alerts, and Discord webhook notifications. Verify alert delivery through automated tests and a live webhook test.

---

## Tasks Completed

| Task | Tool / Library | Status |
|------|----------------|--------|
| Implemented Alert Manager module (`alert_manager.py`) | Python / Requests | Completed |
| Added severity-based alert formatting with timestamps | Python | Completed |
| Integrated Discord webhook for automated alerting | Discord Webhooks | Completed |
| Added fallback mode when webhook is not configured (CI-safe) | Python | Completed |
| Wrote unit tests for alert dispatch logic | pytest | Completed |
| Mocked network calls for safe automated testing | pytest / monkeypatch | Completed |
| Performed manual alert dispatch using live Discord webhook | Discord | Completed |
| Updated `.env.example` with `DISCORD_WEBHOOK_URL` | Environment Config | Completed |

---

## Deliverables

| Deliverable | Description |
|-------------|-------------|
| Alert Manager (`app/utils/alert_manager.py`) | Handles formatting, dispatching, and CI fallback |
| Unit Tests (`tests/test_alert_manager.py`) | Validates behavior with and without webhook |
| Updated `.env.example` | Includes `DISCORD_WEBHOOK_URL` for easy setup |
| Screenshot of Discord alert (`docs/screenshots/week4_discord.png`) |

---

## Verification and Results

### Manual Alert Test
```python
from app.utils.alert_manager import send_alert
send_alert(
    "Manual Week 4 alert test",
    severity="info",
    source="manual_test"
) 
---

**Result:** Alert successfully delivered to Discord.

### Automated Test Results
**Command executed:**
```bash
pytest -q
