# DLP Metadata Integration Changes

## Summary

This implementation ensures that when DLP middleware detects and redacts sensitive data, that metadata is properly passed to the route/logging layer so database logs show accurate DLP enforcement.

## Files Modified

### 1. `app/middleware/dlp_filter.py`
- Added DLP metadata storage on `request.state` when sensitive data is detected
- Metadata includes: detection status, entities found, redaction status, policy decision, risk score, and severity

### 2. `app/routes/ai.py`
- Updated logging to read DLP metadata from `request.state`
- When DLP is detected in middleware, logs show accurate enforcement information:
  - `redacted=True`
  - `policy_decision="redact"`
  - `severity="high"`
  - `risk_score > 0`
  - `rules_triggered` populated with detected entities

## Verification

Database logs now clearly show DLP enforcement when sensitive data is detected, providing better observability and compliance tracking.