# CyberOracle Compliance Monitor Report

## Overview

This document describes the Compliance Monitor implementation for the CyberOracle senior design project. The monitor provides real-time evidence of security controls for HIPAA and FERPA compliance through a Grafana dashboard.

---

## Dashboard Created

### Name
**CyberOracle Compliance Monitor**

### Location
`grafana/dashboards/cyberoracle_compliance_dashboard.json`

### Dashboard Features

| Panel ID | Title | Type | Purpose |
|----------|-------|------|---------|
| 1 | Total Requests (24h) | Stat | AU-2 audit event volume |
| 2 | Blocked Requests (24h) | Stat | SI-3/4 security actions |
| 3 | Redacted Requests (24h) | Stat | DLP masking actions |
| 4 | High Severity Events (24h) | Stat | SI-4 incident detection |
| 5 | HIPAA-Related Events (24h) | Stat | HIPAA privacy protection |
| 6 | FERPA-Related Events (24h) | Stat | FERPA educational records |
| 7 | Policy Decisions Distribution | Pie Chart | Control distribution view |
| 8 | Policy Decisions Over Time | Timeseries | Temporal control analysis |
| 9 | HIPAA Events Over Time | Timeseries | PHI detection timeline |
| 10 | FERPA Events Over Time | Timeseries | Student data protection |
| 11 | High Severity Over Time | Timeseries | Incident detection timeline |
| 12 | Top Endpoints by Volume | Table | Endpoint activity analysis |
| 13 | Recent High Severity Events | Table | Incident list for audit |
| 14 | Compliance Evidence Mapping | Text | NIST 800-53 control mapping |

---

## Data Source

### Database
- **Type**: PostgreSQL 16
- **Container**: `cyberoracle-db` (from docker-compose.yml)
- **Database**: `cyberoracle`
- **Table**: `logs` (LogEntry model)

### Grafana Configuration
- **Datasource**: `postgres` (configured in `grafana/provisioning/datasources/postgres.yml`)
- **Query Type**: Raw SQL queries against `logs` table
- **Query Format**: PostgreSQL-compatible SQL

### Log Entry Schema (Required Fields)

| Field | Type | Purpose |
|-------|------|---------|
| `endpoint` | String | Endpoint activity tracking |
| `policy_decision` | String | "allow", "redact", or "block" |
| `frameworks` | String | Detected frameworks (HIPAA, FERPA) |
| `severity` | String | "low", "medium", "high" |
| `risk_score` | Float | Risk score for high severity detection |
| `created_at` | DateTime | Timestamp for time-series queries |

---

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `grafana/dashboards/cyberoracle_compliance_dashboard.json` | **MODIFIED** | Complete rewrite of dashboard with compliance-focused panels |
| `reports/compliance-monitor-report.md` | **CREATED** | This documentation file |

---

## Files Already Present (No Changes Required)

| File | Purpose |
|------|---------|
| `grafana/provisioning/datasources/postgres.yml` | PostgreSQL datasource configuration |
| `grafana/provisioning/dashboards/dashboards.yml` | Dashboard provisioning |
| `docker-compose.yml` | PostgreSQL service definition |
| `app/models.py` | LogEntry model definition |
| `app/routes/metrics.py` | Compliance API endpoint |
| `app/services/compliance_engine.py` | HIPAA/FERPA detection logic |
| `app/policies/compliance_policies.py` | Policy configuration |

---

## How It Satisfies the Compliance Monitor Requirement

### 1. Real-Time Monitoring Evidence
- Dashboard refreshes every 30 seconds
- PostgreSQL provides persistent, queryable log data
- Grafana visualizes security control activity in real-time

### 2. HIPAA Compliance Evidence
- **HIPAA-Related Events** panel tracks PHI detection
- Detection logic uses: SSN patterns, medical keywords (patient, diagnosis, treatment, medical)
- **High severity** classification (risk_score >= 0.7) for PHI events
- Policy decision = "block" for PHI protection

### 3. FERPA Compliance Evidence
- **FERPA-Related Events** panel tracks educational record detection
- Detection logic uses: keywords (student, gpa, transcript, grade, @unt.edu)
- **Medium severity** classification for FERPA events
- Policy decision = "redact" for educational records

### 4. Audit Trail Completeness (NIST 800-53 AU-2, AU-3)
- Total requests panel shows audit event collection
- Top endpoints panel shows endpoint-level audit trails
- All events logged with timestamps to PostgreSQL

### 5. Security Monitoring (NIST 800-53 SI-3, SI-4)
- Blocked/redacted requests show security action execution
- High severity events show incident detection
- Policy decisions over time shows control activity

### 6. Demonstration Value
- **Live, demoable dashboard** with real data queries
- **No mock data required** - queries against actual logs table
- **Clear compliance mapping** in panel 14 for reviewers
- **Adjustable time ranges** via Grafana UI (1h, 6h, 12h, 24h, 7d, 30d)

---

## Accessing the Dashboard

### Local Development
1. Start the stack:
   ```bash
   docker-compose up -d
   ```
2. Open Grafana: `http://localhost:3000`
3. Login:
   - Username: `admin`
   - Password: `admin` (from docker-compose.yml environment)
4. Navigate to: **Dashboards** → **CyberOracle** → **CyberOracle Compliance Monitor**

### With Sample Data
To populate the dashboard with test events:
```bash
# Create logs with HIPAA events
curl -X POST http://localhost:8000/api/documents/sanitize \
  -H "Content-Type: application/json" \
  -d '{"text": "Patient John Doe SSN 123-45-6789 diagnosis treatment"}'

# Create logs with FERPA events
curl -X POST http://localhost:8000/api/documents/sanitize \
  -H "Content-Type: application/json" \
  -d '{"text": "Student ID 12345 GPA 3.85 transcript grade"}'

# Create general events
curl -X POST http://localhost:8000/api/documents/sanitize \
  -H "Content-Type: application/json" \
  -d '{"text": "Normal request without sensitive data"}'
```

---

## Screenshots for Final Report/Demo

### Recommended Screenshots

| # | Description | Action Required |
|---|-------------|-----------------|
| 1 | **Dashboard Home** - Shows all 14 panels at a glance | Open dashboard, scroll to see panels 1-7 (top row) |
| 2 | **Compliance Evidence Mapping** - Panel 14 explains NIST controls | Scroll to bottom, screenshot the markdown panel |
| 3 | **HIPAA/FERPA Event Panels** - Show HIPAA panel highlighted | Click on HIPAA panel, show query results |
| 4 | **Policy Decisions Over Time** - Panel 8 shows temporal analysis | Show timeseries panel with multiple lines |
| 5 | **Recent High Severity Events** - Panel 13 shows incident list | Show table with red-highlighted rows |
| 6 | **Top Endpoints Table** - Panel 12 shows activity per endpoint | Show table with blocked/redacted columns |

### To Take Screenshots

```bash
# Start the stack
cd "C:\Users\Bishesh Dulal\Documents\Project\School\Capstone\CyberOracle"
docker-compose up -d

# Wait for services
sleep 30

# Generate sample data
curl -X POST http://localhost:8000/api/documents/sanitize \
  -H "Content-Type: application/json" \
  -d '{"text": "Patient John SSN 123-45-6789 medical diagnosis"}'

curl -X POST http://localhost:8000/api/documents/sanitize \
  -H "Content-Type: application/json" \
  -d '{"text": "Student ID 98765 GPA 4.0 transcript"}'

# Open Grafana in browser and take screenshots
# http://localhost:3000 → Login as admin/admin
```

---

## Compliance Control Mapping Summary

| NIST 800-53 Control | Dashboard Panel | Evidence Provided |
|---------------------|-----------------|-------------------|
| **AU-2** (Audit Events) | Total Requests | Confirms audit event collection |
| **AU-3** (Audit Record Selection) | Top Endpoints Table | Shows which endpoints generate logs |
| **AU-6** (Audit Review) | Recent High Severity Events | Lists high-risk incidents for review |
| **SI-3** (Security Filtering) | Blocked/Redacted Requests | Shows filtering actions executed |
| **SI-4** (Monitoring) | All time-series panels | Real-time monitoring evidence |
| **HIPAA Privacy Rule** | HIPAA Events | PHI detection and blocking |
| **FERPA §99.31** | FERPA Events | Educational record detection |

---

## Conclusion

The **CyberOracle Compliance Monitor** satisfies the senior design project requirement for a compliance monitoring system by:

1. ✅ Providing a **real-time Grafana dashboard** with 14 compliance-focused panels
2. ✅ Querying **actual PostgreSQL data** for evidence-based reporting
3. ✅ Tracking **HIPAA and FERPA** related events specifically
4. ✅ Mapping panels to **NIST 800-53 controls** for compliance justification
5. ✅ Offering **live demonstration capability** with sample data generation

The implementation is **minimal and defensible** - no architecture changes, no fake integrations, just a focused dashboard that proves compliance controls are operating as designed.
