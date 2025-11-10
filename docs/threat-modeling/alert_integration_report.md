# CyberOracle – Week 4 Alert Integration Report  
**Author:** Pradip Sapkota  
**Date:** Nov 22 2025  
**Scope:** AlertManager + Discord Integration

---

## Objective  
Implement and validate CyberOracle’s real-time alerting pipeline that triggers notifications to Discord whenever DLP or Presidio detects sensitive data.

---

## Implementation Overview
- **Module:** `app/utils/alert_manager.py`  
- **Alert Source:** Presidio DLP + manual system tests  
- **Channel:** Discord Webhook (securely stored in `DISCORD_WEBHOOK_URL`)  
- **Supported Severities:** `info`, `warning`, `critical`  

### Alert Flow Diagram

- Presidio → AlertManager → Discord Webhook → #cyberoracle-alerts


---

## Validation Results
| Test Case | Expected Behavior | Result |
|------------|------------------|---------|
| Presidio detects SSN | Alert in Discord | ✅ |
| Presidio detects API key | Alert in Discord | ✅ |
| Manual test (`python3 scripts/test_alerts.py`) | Info / Warning / Critical alerts sent | ✅ |
| Unit tests (`pytest tests/test_alert_manager.py`) | All pass (2/2) | ✅ |

---

## Observations
- Alerts delivered within **1 s** to Discord.  
- Proper formatting with emoji + timestamp.  
- No duplicate or failed deliveries.  
- Secure webhook hidden via environment variable.  

---

## Outcome  
| Deliverable | Status |
|--------------|---------|
| Discord integration functional | ✅ |
| Presidio → Alert pipeline working | ✅ |
| Unit & functional tests passing | ✅ |
| Documentation prepared | ✅ (Week 4 Deliverable Complete) |

---

**Next Step (Week 5–6):**  
- Merge Presidio + Regex DLP into unified DLP v2.  
- Configure Grafana dashboards for API metrics + alerts.
