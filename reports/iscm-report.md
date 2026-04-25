# ISCM Report: InfoSec Continuous Monitoring

## Overview

This document describes the ISCM (InfoSec Continuous Monitoring) implementation for the CyberOracle senior design project, based on the existing Compliance Monitor dashboard.

---

## What ISCM Means in This System

**ISCM (InfoSec Continuous Monitoring)** according to NIST SP 800-137 is a framework for continuous security monitoring and assessment of organizational security controls.

In the CyberOracle system, ISCM is realized through:

1. **Continuous Data Collection**: All API requests are logged to PostgreSQL with timestamps
2. **Automated Security Analysis**: Real-time queries analyze DLP outcomes, policy decisions, and compliance framework detection
3. **Real-Time Visualization**: Grafana dashboard refreshes every 30 seconds
4. **Alerting Mechanism**: High-severity events and alerts are tracked and displayed
5. **Audit Trail**: Persistent log storage enables forensic analysis

### Key ISCM Principles Implemented

| Principle | Implementation |
|-----------|----------------|
| **Automation** | Automated PostgreSQL queries via Grafana provisioning |
| **Integration** | Single dashboard showing compliance + security metrics |
| **Real-time** | 30-second refresh interval for live monitoring |
| **Continuous** | 24-hour rolling window with adjustable time ranges |
| **Actionable** | Alert counts and incident tables enable rapid response |

---

## Metrics Continuously Monitored

### Security Metrics

| Metric | Panel ID | Description | Threshold Alert |
|--------|----------|-------------|-----------------|
| Total Requests | 1, 16 | Baseline traffic volume | N/A |
| Blocked Requests | 2 | DLP security actions | Any count = monitoring |
| Redacted Requests | 3 | DLP masking actions | Any count = monitoring |
| High Severity Events | 4, 11 | risk_score >= 0.7 | >0 triggers review |

### Compliance Metrics

| Metric | Panel ID | Framework | Description |
|--------|----------|-----------|-------------|
| HIPAA Events | 5, 9 | HIPAA | PHI detection (SSN, medical keywords) |
| FERPA Events | 6, 10 | FERPA | Educational records (student, GPA, transcript) |
| Policy Decisions | 7, 8 | All | Distribution of allow/redact/block |

### Alerting Metrics

| Metric | Panel ID | Description |
|--------|----------|-------------|
| Total Alerts Triggered | 15 | Count of high-severity events |
| Recent High Severity | 13 | Detailed incident list for forensics |

### Operational Metrics

| Metric | Panel ID | Description |
|--------|----------|-------------|
| Log Volume Over Time | 14 | System activity timeline |
| Top Endpoints | 12 | Attack surface visibility |

---

## How Grafana Dashboard Proves Continuous Monitoring

### 1. Real-Time Data Freshness

```json
"refresh": "30s"
```

- Dashboard automatically refreshes every 30 seconds
- All panels show current 24-hour metrics
- Demonstrates **continuous** rather than **periodic** monitoring

### 2. Persistent Log Collection

```sql
SELECT COUNT(*)::bigint AS value FROM logs WHERE created_at >= NOW() - INTERVAL '24 hours';
```

- All queries source from PostgreSQL `logs` table
- Timestamps ensure audit trail integrity
- Demonstrates **automated collection**

### 3. Temporal Analysis

```sql
SELECT date_trunc('minute', created_at) AS time, COUNT(*)::bigint AS value
FROM logs WHERE ... GROUP BY 1 ORDER BY 1;
```

- Panel 8, 9, 10, 11 all show time-series data
- Enables detection of security incidents over time
- Demonstrates **continuous temporal monitoring**

### 4. Alerting Capability

```sql
SELECT COUNT(*)::bigint AS value FROM logs
WHERE (severity = 'high' OR risk_score >= 0.7)
AND created_at >= NOW() - INTERVAL '24 hours';
```

- Panel 15 tracks alert count
- Panel 13 shows recent incidents with details
- Demonstrates **alerting and notification capability**

---

## Panels Demonstrating ISCM

### Critical ISCM Panels

| Panel ID | Title | ISCM Evidence |
|----------|-------|---------------|
| **15** | Total Alerts Triggered (24h) | **NEW** - Alert count for incident response |
| **14** | Log Volume Over Time (All Events) | **NEW** - System activity monitoring |
| **16** | Log Volume (Last 24h) | **NEW** - Baseline traffic indicator |
| 1 | Total Requests (24h) | Baseline monitoring |
| 2 | Blocked Requests (24h) | Security control execution |
| 3 | Redacted Requests (24h) | DLP control execution |
| 4 | High Severity Events (24h) | Incident detection |
| 5 | HIPAA-Related Events (24h) | PHI protection monitoring |
| 6 | FERPA-Related Events (24h) | Educational records protection |
| 7 | Policy Decisions Distribution | Control outcome visualization |
| 8 | Policy Decisions Over Time | Temporal security analysis |
| 9 | HIPAA Events Over Time | PHI timeline monitoring |
| 10 | FERPA Events Over Time | Student data timeline |
| 11 | High Severity Events Over Time | Incident timeline |
| 12 | Top Endpoints by Request Volume | Attack surface visibility |
| 13 | Recent High Severity Events | Forensic investigation support |
| 17 | ISCM View - InfoSec Continuous Monitoring | **NEW** - ISCM documentation panel |

---

## ISCM NIST SP 800-137 Requirements Mapping

| NIST ISCM Requirement | Dashboard Evidence |
|----------------------|--------------------|
| **Continuous Security Monitoring** | All panels refresh every 30 seconds |
| **Security Control Assessment** | Panels 2, 3, 7 show DLP control outcomes |
| **Security Impact Analysis** | Panel 11 shows high-severity trends |
| **System State Monitoring** | Panel 14 shows overall log volume |
| **Automated Monitoring** | Grafana provisions dashboard automatically |
| **Alerting** | Panel 15 tracks alerts, Panel 13 shows incidents |
| **Audit Trail** | All data from PostgreSQL logs table |

---

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `grafana/dashboards/cyberoracle_compliance_dashboard.json` | **MODIFIED** | Added ISCM section (panels 14, 15, 16, 17), renamed title to include "ISCM" |
| `reports/iscm-report.md` | **CREATED** | ISCM documentation explaining metrics and NIST mapping |

### New Panels Added

| Panel ID | Title | Purpose |
|----------|-------|---------|
| 14 | Log Volume Over Time (All Events) | Shows overall system activity timeline |
| 15 | Total Alerts Triggered (24h) | Counts high-severity events for alerting |
| 16 | Log Volume (Last 24h) | Stat panel showing total request count |
| 17 | ISCM View - InfoSec Continuous Monitoring | Documentation panel explaining ISCM |

---

## What Screenshots to Take

### Essential Screenshots for Final Report/Demo

| # | Panel Focus | Description | Action Required |
|---|-------------|-------------|-----------------|
| 1 | **ISCM View Panel (17)** | Shows NIST mapping and ISCM principles | Scroll to bottom of dashboard, screenshot the markdown panel |
| 2 | **Alerts Panel (15)** | Shows alert count for incident tracking | Show Panel 15 with stat visualization |
| 3 | **Log Volume Timeline (14)** | Shows system activity over time | Click Panel 14 to show timeseries |
| 4 | **Security Panels (1, 2, 3, 4)** | Top row shows all security metrics | Screenshot top 2 rows showing stat panels |
| 5 | **High Severity Timeline (11)** | Shows incident trends | Click Panel 11 to show timeseries with color coding |
| 6 | **Recent Incidents (13)** | Table of high-severity events for forensics | Show Panel 13 with incident details |

### To Generate Sample Data and Capture Screenshots

```bash
# Start the stack
cd "C:\Users\Bishesh Dulal\Documents\Project\School\Capstone\CyberOracle"
docker-compose up -d

# Wait for services to start
sleep 30

# Generate HIPAA events (high severity)
curl -X POST http://localhost:8000/api/documents/sanitize \
  -H "Content-Type: application/json" \
  -d '{"text": "Patient SSN 123-45-6789 diagnosis treatment medical"}'

# Generate FERPA events (medium severity)
curl -X POST http://localhost:8000/api/documents/sanitize \
  -H "Content-Type: application/json" \
  -d '{"text": "Student ID 98765 GPA 3.95 transcript grade"}'

# Generate general events
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/documents/sanitize \
    -H "Content-Type: application/json" \
    -d '{"text": "General request without sensitive data"}'
done

# Open Grafana
# http://localhost:3000
# Login: admin / admin
```

### Screenshot Sequence

1. **Dashboard Overview** - Show full ISCM dashboard with all panels
2. **ISCM Documentation Panel** - Scroll to Panel 17 showing NIST mapping
3. **Alerts Panel** - Show Panel 15 with alert count
4. **Timeline Analysis** - Click Panel 14 or 11 to show timeseries
5. **Incident Details** - Show Panel 13 with high-severity event table

---

## Final Report Wording

### For Senior Design Report - ISCM Section

> **InfoSec Continuous Monitoring (ISCM)**
>
> The CyberOracle system implements ISCM per NIST SP 800-137 through a real-time Grafana dashboard that continuously monitors security controls and compliance posture. The dashboard provides:
>
> 1. **Real-time monitoring**: 30-second refresh interval ensures current visibility into security events
> 2. **Automated collection**: All metrics are queried from PostgreSQL logs table via Grafana provisioning
> 3. **Alerting capability**: Panel 15 tracks alert counts; Panel 13 provides incident details for response
> 4. **Temporal analysis**: Time-series panels (8, 9, 10, 11, 14) enable detection of security incidents over time
> 5. **Comprehensive coverage**: Security metrics (blocked/redacted requests), compliance metrics (HIPAA/FERPA), and operational metrics (log volume, endpoint activity)
>
> The ISCM dashboard demonstrates continuous security monitoring capabilities for HIPAA and FERPA compliance, with all data sourced from persistent audit logs.

---

## Conclusion

The CyberOracle ISCM implementation demonstrates **InfoSec Continuous Monitoring** by:

1. ✅ **Continuous monitoring** - 30-second refresh provides real-time visibility
2. ✅ **Automated data collection** - Grafana provisions PostgreSQL queries automatically
3. ✅ **Alerting mechanism** - Panels 14, 15, 16 track system activity and alerts
4. ✅ **NIST SP 800-137 compliance** - Full mapping of ISCM requirements to dashboard panels
5. ✅ **Actionable evidence** - Alert counts, incident tables, and temporal analysis enable response

This ISCM implementation leverages the existing Compliance Monitor dashboard with **minimal changes** - just 4 new panels and a documentation panel, no new services or architecture changes.
