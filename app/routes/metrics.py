# app/routes/metrics.py

# This is all mock data for now, so our dashboard can work even before we wire real metrics.

from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/api", tags=["metrics"])


@router.get("/metrics/summary")
async def get_metrics_summary():
    """
    Summary numbers for the main dashboard.
    TODO: replace mock numbers with real DB / log queries.
    """
    return {
        "total_prompts_24h": 486,
        "blocked_prompts": 23,
        "redacted_outputs": 51,
        "high_risk_events": 7,
        "active_models": 4,
    }


@router.get("/compliance/status")
async def get_compliance_status():
    """
    Overall compliance score & control coverage.
    """
    return {
        "compliance_score": 0.82,  # 0–1
        "compliant_controls": 41,
        "total_controls": 50,
    }


@router.get("/alerts/recent")
async def get_recent_alerts():
    """
    Recent security alerts to show on the dashboard.
    """
    return {
        "alerts": [
            {
                "id": "1",
                "type": "Prompt Injection",
                "severity": "High",
                "message": "System prompt extraction attempt detected",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
            {
                "id": "2",
                "type": "Model Misuse",
                "severity": "Medium",
                "message": "Unauthorized model requested by support-bot role",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
            {
                "id": "3",
                "type": "Data Exfiltration",
                "severity": "High",
                "message": "Possible PHI leak blocked by DLP",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        ]
    }
