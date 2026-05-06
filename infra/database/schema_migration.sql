-- Schema Migration Script for CyberOracle Logs Table
-- Version: 1.0
-- Date: 2026-05-06
-- Purpose: Ensure all required columns exist for Grafana compliance dashboards
--
-- This script is idempotent - safe to run multiple times.

-- Add missing columns if they don't exist (safe to run repeatedly)
ALTER TABLE logs ADD COLUMN IF NOT EXISTS event_type VARCHAR;
ALTER TABLE logs ADD COLUMN IF NOT EXISTS frameworks VARCHAR;
ALTER TABLE logs ADD COLUMN IF NOT EXISTS decision VARCHAR;
ALTER TABLE logs ADD COLUMN IF NOT EXISTS severity VARCHAR;
ALTER TABLE logs ADD COLUMN IF NOT EXISTS risk_score DOUBLE PRECISION;
ALTER TABLE logs ADD COLUMN IF NOT EXISTS source VARCHAR;
ALTER TABLE logs ADD COLUMN IF NOT EXISTS policy_decision VARCHAR;
ALTER TABLE logs ADD COLUMN IF NOT EXISTS integrity_hash VARCHAR;

-- Add indexes for query performance (Grafana dashboards)
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);
CREATE INDEX IF NOT EXISTS idx_logs_policy_decision ON logs(policy_decision);
CREATE INDEX IF NOT EXISTS idx_logs_severity ON logs(severity);
CREATE INDEX IF NOT EXISTS idx_logs_frameworks ON logs(frameworks) WHERE frameworks IS NOT NULL;

-- Optional: Add partial indexes for specific compliance checks
-- These speed up dashboard queries that filter by framework
CREATE INDEX IF NOT EXISTS idx_logs_hipaa ON logs(created_at) WHERE frameworks LIKE '%HIPAA%';
CREATE INDEX IF NOT EXISTS idx_logs_ferpa ON logs(created_at) WHERE frameworks LIKE '%FERPA%';
