"""
tests/test_anomaly_alerting.py

Unit tests for scripts/anomaly_alerting.py (PSFR6).
Tests all four anomaly detection functions with synthetic log data.
No real HTTP calls or DB writes — external calls are mocked.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.anomaly_alerting import (  # noqa: E402
    check_rate_anomaly,
    check_payload_anomaly,
    check_high_risk,
    check_repeated_blocks,
    RATE_THRESHOLD,
    PAYLOAD_SIZE_THRESHOLD,
    RISK_SCORE_THRESHOLD,
    BLOCK_REPEAT_THRESHOLD,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_log(
    message="", policy_decision="allow", risk_score=0.0, id=1, endpoint="/ai/query"
):
    return {
        "id": id,
        "message": message,
        "policy_decision": policy_decision,
        "risk_score": risk_score,
        "endpoint": endpoint,
    }


def _ip_log(ip: str, **kwargs):
    return _make_log(message=f"{{'client_ip': '{ip}', 'other': 'data'}}", **kwargs)


# ---------------------------------------------------------------------------
# check_rate_anomaly
# ---------------------------------------------------------------------------


def test_rate_anomaly_detects_ip_over_threshold():
    ip = "10.0.0.1"
    logs = [_ip_log(ip) for _ in range(RATE_THRESHOLD + 1)]
    result = check_rate_anomaly(logs)
    assert len(result) == 1
    assert result[0]["ip"] == ip
    assert result[0]["count"] == RATE_THRESHOLD + 1


def test_rate_anomaly_no_flag_at_threshold():
    ip = "10.0.0.2"
    logs = [_ip_log(ip) for _ in range(RATE_THRESHOLD)]
    result = check_rate_anomaly(logs)
    assert result == []


def test_rate_anomaly_empty_logs():
    assert check_rate_anomaly([]) == []


def test_rate_anomaly_ignores_logs_without_ip():
    logs = [_make_log(message="no ip here") for _ in range(20)]
    assert check_rate_anomaly(logs) == []


def test_rate_anomaly_multiple_ips():
    logs = (
        [_ip_log("1.1.1.1") for _ in range(RATE_THRESHOLD + 2)]
        + [_ip_log("2.2.2.2") for _ in range(RATE_THRESHOLD + 1)]
        + [_ip_log("3.3.3.3") for _ in range(2)]  # under threshold
    )
    result = check_rate_anomaly(logs)
    ips = {r["ip"] for r in result}
    assert "1.1.1.1" in ips
    assert "2.2.2.2" in ips
    assert "3.3.3.3" not in ips


# ---------------------------------------------------------------------------
# check_payload_anomaly
# ---------------------------------------------------------------------------


def test_payload_anomaly_detects_large_input():
    big_input = "A" * (PAYLOAD_SIZE_THRESHOLD + 1)
    log = _make_log(message=f"{{'input_preview': '{big_input}'}}", id=42)
    result = check_payload_anomaly([log])
    assert len(result) == 1
    assert result[0]["id"] == 42
    assert result[0]["size"] > PAYLOAD_SIZE_THRESHOLD


def test_payload_anomaly_no_flag_at_threshold():
    exact_input = "B" * PAYLOAD_SIZE_THRESHOLD
    log = _make_log(message=f"{{'input_preview': '{exact_input}'}}")
    result = check_payload_anomaly([log])
    assert result == []


def test_payload_anomaly_empty_logs():
    assert check_payload_anomaly([]) == []


def test_payload_anomaly_ignores_logs_without_preview():
    log = _make_log(message="no input_preview field here")
    assert check_payload_anomaly([log]) == []


def test_payload_anomaly_preview_truncated_to_100():
    big_input = "C" * (PAYLOAD_SIZE_THRESHOLD + 200)
    log = _make_log(message=f"{{'input_preview': '{big_input}'}}")
    result = check_payload_anomaly([log])
    assert result[0]["preview"].endswith("...")
    assert len(result[0]["preview"]) == 103  # 100 chars + "..."


# ---------------------------------------------------------------------------
# check_high_risk
# ---------------------------------------------------------------------------


def test_high_risk_detects_above_threshold():
    log = _make_log(risk_score=RISK_SCORE_THRESHOLD, id=10)
    result = check_high_risk([log])
    assert len(result) == 1
    assert result[0]["id"] == 10


def test_high_risk_no_flag_below_threshold():
    log = _make_log(risk_score=RISK_SCORE_THRESHOLD - 0.01)
    assert check_high_risk([log]) == []


def test_high_risk_none_risk_score_skipped():
    log = _make_log(risk_score=None)
    assert check_high_risk([log]) == []


def test_high_risk_empty_logs():
    assert check_high_risk([]) == []


def test_high_risk_returns_correct_fields():
    log = _make_log(risk_score=0.9, id=7, endpoint="/ai/query", policy_decision="block")
    result = check_high_risk([log])
    assert result[0]["risk_score"] == 0.9
    assert result[0]["endpoint"] == "/ai/query"
    assert result[0]["decision"] == "block"


# ---------------------------------------------------------------------------
# check_repeated_blocks
# ---------------------------------------------------------------------------


def test_repeated_blocks_detects_ip_at_threshold():
    ip = "192.168.1.1"
    logs = [_ip_log(ip, policy_decision="block") for _ in range(BLOCK_REPEAT_THRESHOLD)]
    result = check_repeated_blocks(logs)
    assert len(result) == 1
    assert result[0]["ip"] == ip
    assert result[0]["blocks"] == BLOCK_REPEAT_THRESHOLD


def test_repeated_blocks_no_flag_below_threshold():
    ip = "192.168.1.2"
    logs = [
        _ip_log(ip, policy_decision="block") for _ in range(BLOCK_REPEAT_THRESHOLD - 1)
    ]
    assert check_repeated_blocks(logs) == []


def test_repeated_blocks_ignores_allow_decisions():
    ip = "192.168.1.3"
    logs = [_ip_log(ip, policy_decision="allow") for _ in range(10)]
    assert check_repeated_blocks(logs) == []


def test_repeated_blocks_empty_logs():
    assert check_repeated_blocks([]) == []


def test_repeated_blocks_ignores_logs_without_ip():
    logs = [_make_log(message="no ip", policy_decision="block") for _ in range(10)]
    assert check_repeated_blocks(logs) == []
