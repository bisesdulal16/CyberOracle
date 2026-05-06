'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { apiFetch } from '../lib/auth';
import {
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ShieldCheckIcon,
  BoltIcon,
} from '@heroicons/react/24/outline';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8001';

type IscmStatus = {
  assessed_at: string;
  monitoring_health: 'healthy' | 'warning' | 'degraded';
  compliance: { score: number; total_events: number; allowed_events: number };
  threat_indicators: { level: string; high_risk_events_1h: number; blocked_requests_1h: number };
  log_integrity: { total_entries: number; integrity_hashed: number; coverage: number };
  activity_24h: { total_requests: number; log_promotions: number };
  data_protection: { encryption_at_rest: boolean; encryption_in_transit: boolean };
  alert_channels: { discord: boolean; slack: boolean; email: boolean };
};

type PromotionResult = {
  promoted_at: string;
  window_hours: number;
  promoted_count: number;
  promoted_entries: Array<{
    id: number;
    event_type: string | null;
    severity: string | null;
    risk_score: number | null;
    source: string | null;
    endpoint: string;
    created_at: string | null;
  }>;
};

function healthColor(health: string) {
  if (health === 'healthy') return 'text-green-400';
  if (health === 'warning') return 'text-amber-400';
  return 'text-red-400';
}

function healthIcon(health: string) {
  if (health === 'healthy') return <CheckCircleIcon className="w-5 h-5 text-green-400" />;
  if (health === 'warning') return <ExclamationTriangleIcon className="w-5 h-5 text-amber-400" />;
  return <XCircleIcon className="w-5 h-5 text-red-400" />;
}

function threatBadge(level: string) {
  if (level === 'none') return 'bg-green-500/10 text-green-400 border-green-500/20';
  if (level === 'low') return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
  if (level === 'medium') return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
  return 'bg-red-500/10 text-red-400 border-red-500/20';
}

export default function MonitoringPanel() {
  const [status, setStatus] = useState<IscmStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [statusError, setStatusError] = useState<string | null>(null);

  const [promoting, setPromoting] = useState(false);
  const [promotionResult, setPromotionResult] = useState<PromotionResult | null>(null);
  const [promotionError, setPromotionError] = useState<string | null>(null);

  const fetchStatus = useCallback(() => {
    setStatusLoading(true);
    setStatusError(null);
    apiFetch(`${API_BASE}/api/iscm/status`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => setStatus(d))
      .catch(() => setStatusError('Failed to load ISCM status.'))
      .finally(() => setStatusLoading(false));
  }, []);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  function runPromotion() {
    setPromoting(true);
    setPromotionError(null);
    setPromotionResult(null);
    apiFetch(`${API_BASE}/api/logs/promote?window_hours=24`, { method: 'POST' })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { setPromotionResult(d); fetchStatus(); })
      .catch(() => setPromotionError('Log promotion failed.'))
      .finally(() => setPromoting(false));
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">ISCM — Continuous Monitoring</h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Information Systems Continuous Monitoring posture. DoD DevSecOps Monitor phase.
          </p>
        </div>
        <button
          onClick={fetchStatus}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm transition"
        >
          <ArrowPathIcon className={`w-4 h-4 ${statusLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {statusError && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {statusError}
        </div>
      )}

      {statusLoading && !statusError && (
        <div className="text-sm text-slate-500">Loading ISCM status…</div>
      )}

      {status && (
        <>
          {/* Health Banner */}
          <div className="rounded-xl border border-slate-700 bg-slate-900 px-5 py-4 flex items-center gap-3">
            {healthIcon(status.monitoring_health)}
            <div>
              <p className={`font-semibold capitalize ${healthColor(status.monitoring_health)}`}>
                Monitoring health: {status.monitoring_health}
              </p>
              <p className="text-xs text-slate-500 mt-0.5">
                Assessed {new Date(status.assessed_at).toLocaleString()}
              </p>
            </div>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard label="Compliance Score" value={`${(status.compliance.score * 100).toFixed(1)}%`} />
            <StatCard label="Threat Level" value={status.threat_indicators.level.toUpperCase()} colorClass={threatBadge(status.threat_indicators.level)} />
            <StatCard label="Log Integrity" value={`${(status.log_integrity.coverage * 100).toFixed(1)}%`} />
            <StatCard label="Requests 24h" value={String(status.activity_24h.total_requests)} />
          </div>

          {/* Detail cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {/* Threat Indicators */}
            <DetailCard title="Threat Indicators (1h)">
              <Row label="High-risk events" value={status.threat_indicators.high_risk_events_1h} />
              <Row label="Blocked requests" value={status.threat_indicators.blocked_requests_1h} />
              <Row label="Threat level" value={status.threat_indicators.level} />
            </DetailCard>

            {/* Log Integrity */}
            <DetailCard title="Log Integrity">
              <Row label="Total entries" value={status.log_integrity.total_entries} />
              <Row label="Integrity-hashed" value={status.log_integrity.integrity_hashed} />
              <Row label="Coverage" value={`${(status.log_integrity.coverage * 100).toFixed(1)}%`} />
            </DetailCard>

            {/* Data Protection */}
            <DetailCard title="Data Protection">
              <BoolRow label="Encryption at rest" value={status.data_protection.encryption_at_rest} />
              <BoolRow label="Encryption in transit" value={status.data_protection.encryption_in_transit} />
            </DetailCard>

            {/* Alert Channels */}
            <DetailCard title="Alert Channels">
              <BoolRow label="Discord" value={status.alert_channels.discord} />
              <BoolRow label="Slack" value={status.alert_channels.slack} />
              <BoolRow label="Email" value={status.alert_channels.email} />
            </DetailCard>
          </div>

          {/* Log Promotion */}
          <div className="rounded-xl border border-slate-700 bg-slate-900 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                  <BoltIcon className="w-4 h-4 text-cyan-400" />
                  Log Promotion
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Escalate high-risk log entries (risk ≥ 0.7) to external alert channels
                  and create a traceable promotion audit record.
                </p>
              </div>
              <button
                onClick={runPromotion}
                disabled={promoting}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-sm font-medium transition"
              >
                <ArrowPathIcon className={`w-4 h-4 ${promoting ? 'animate-spin' : ''}`} />
                {promoting ? 'Promoting…' : 'Run Promotion'}
              </button>
            </div>

            {promotionError && (
              <div className="text-sm text-red-400">{promotionError}</div>
            )}

            {promotionResult && (
              <div className="space-y-2">
                <p className="text-sm text-slate-300">
                  <span className="text-cyan-400 font-semibold">{promotionResult.promoted_count}</span>{' '}
                  entr{promotionResult.promoted_count === 1 ? 'y' : 'ies'} promoted
                  {' '}(window: {promotionResult.window_hours}h)
                </p>
                {promotionResult.promoted_entries.length > 0 && (
                  <div className="divide-y divide-slate-800 rounded-lg border border-slate-700 overflow-hidden">
                    {promotionResult.promoted_entries.map((e) => (
                      <div key={e.id} className="flex items-center justify-between px-4 py-2 text-xs">
                        <span className="font-mono text-slate-400">#{e.id}</span>
                        <span className="text-slate-300">{e.event_type ?? '—'}</span>
                        <span className="text-amber-400">{e.risk_score?.toFixed(2) ?? '—'}</span>
                        <span className="text-slate-500">{e.source ?? '—'}</span>
                      </div>
                    ))}
                  </div>
                )}
                {promotionResult.promoted_count === 0 && (
                  <p className="text-sm text-slate-500">
                    No high-risk entries found in the last {promotionResult.window_hours}h window.
                  </p>
                )}
              </div>
            )}

            <div className="flex items-center gap-2 text-xs text-slate-500">
              <ShieldCheckIcon className="w-3.5 h-3.5" />
              Last promotion run:{' '}
              {status.activity_24h.log_promotions > 0
                ? `${status.activity_24h.log_promotions} promotion(s) in last 24h`
                : 'None in last 24h'}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({ label, value, colorClass }: { label: string; value: string; colorClass?: string }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-3">
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className={`text-lg font-bold text-slate-100 ${colorClass ? `px-2 py-0.5 rounded border text-xs font-semibold inline-block ${colorClass}` : ''}`}>
        {value}
      </p>
    </div>
  );
}

function DetailCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 p-4 space-y-2">
      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">{title}</h3>
      {children}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-slate-400">{label}</span>
      <span className="text-slate-100 font-medium">{value}</span>
    </div>
  );
}

function BoolRow({ label, value }: { label: string; value: boolean }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-slate-400">{label}</span>
      {value
        ? <span className="flex items-center gap-1 text-green-400 text-xs"><CheckCircleIcon className="w-3.5 h-3.5" /> Enabled</span>
        : <span className="flex items-center gap-1 text-slate-500 text-xs"><XCircleIcon className="w-3.5 h-3.5" /> Disabled</span>
      }
    </div>
  );
}
