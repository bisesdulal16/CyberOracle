'use client';

import React, { useState, useEffect } from 'react';
import { apiFetch } from '../lib/auth';
import { ArrowDownTrayIcon, ArrowPathIcon, ShieldExclamationIcon, CircleStackIcon } from '@heroicons/react/24/outline';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

// ── Types ─────────────────────────────────────────────────────────────────────

type ReportData = {
  period: { start: string; end: string };
  total_requests: number;
  policy_decisions: { blocked: number; redacted: number; allowed: number };
  severity: { high: number; medium: number; low: number };
  event_type_breakdown: { event_type: string; count: number }[];
  decision_breakdown: { decision: string; count: number }[];
  top_endpoints: { endpoint: string; count: number }[];
};

type ThreatFinding = {
  threat_type: string;
  severity: string;
  description: string;
  affected_count: number;
  source: string;
  recommendation: string;
  remediation_steps: string[];
};

type RemediationReport = {
  generated_at: string;
  analysis_window_hours: number;
  status: string;
  overall_severity: string;
  total_findings: number;
  critical_findings: number;
  findings: ThreatFinding[];
  summary: string;
};

type DbAudit = {
  audit_generated_at: string;
  total_log_entries: number;
  severity_breakdown: { low: number; medium: number; high: number };
  policy_decisions_24h: { allow: number; redact: number; block: number };
  high_risk_events_24h: number;
  database_security: {
    encryption_enabled: boolean;
    encrypted_fields: string[];
    audit_trail_active: boolean;
  };
};

// ── Small helpers ─────────────────────────────────────────────────────────────

function Spinner({ className }: { className?: string }) {
  return <ArrowPathIcon className={`animate-spin text-cyan-400 ${className ?? 'w-5 h-5'}`} />;
}

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}
function sevenDaysAgoStr() {
  const d = new Date();
  d.setDate(d.getDate() - 7);
  return d.toISOString().slice(0, 10);
}

function decisionColor(d: string) {
  const v = d.toLowerCase();
  if (v === 'block') return 'bg-red-400/10 text-red-400';
  if (v === 'redact') return 'bg-amber-400/10 text-amber-400';
  if (v === 'allow') return 'bg-emerald-400/10 text-emerald-400';
  return 'bg-slate-800 text-slate-400';
}

function severityBadge(s: string) {
  const v = s.toLowerCase();
  if (v === 'high' || v === 'critical') return 'bg-red-400/10 text-red-400 border border-red-500/20';
  if (v === 'medium') return 'bg-amber-400/10 text-amber-400 border border-amber-500/20';
  return 'bg-blue-400/10 text-blue-400 border border-blue-500/20';
}

function exportCSV(data: ReportData) {
  const lines: string[][] = [];
  lines.push(['CyberOracle Security Report']);
  lines.push([`Period: ${data.period.start} to ${data.period.end}`]);
  lines.push([]);
  lines.push(['Summary']);
  lines.push(['Total Requests', String(data.total_requests)]);
  lines.push(['Blocked', String(data.policy_decisions.blocked)]);
  lines.push(['Redacted', String(data.policy_decisions.redacted)]);
  lines.push(['Allowed', String(data.policy_decisions.allowed)]);
  lines.push([]);
  lines.push(['Severity Breakdown']);
  lines.push(['High', String(data.severity.high)]);
  lines.push(['Medium', String(data.severity.medium)]);
  lines.push(['Low', String(data.severity.low)]);
  lines.push([]);
  lines.push(['Event Type Breakdown']);
  lines.push(['Event Type', 'Count']);
  data.event_type_breakdown.forEach((r) => lines.push([r.event_type, String(r.count)]));
  lines.push([]);
  lines.push(['Top Endpoints']);
  lines.push(['Endpoint', 'Count']);
  data.top_endpoints.forEach((r) => lines.push([r.endpoint, String(r.count)]));

  const csv = lines.map((row) => row.map((v) => `"${v}"`).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `cyberoracle-report-${data.period.start}-to-${data.period.end}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Shared sub-components ─────────────────────────────────────────────────────

function StatCard({ label, value, sub, color }: { label: string; value: number; sub?: string; color?: string }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <p className="text-xs font-medium text-slate-400 mb-1">{label}</p>
      <p className={`text-2xl font-semibold ${color ?? 'text-slate-100'}`}>{value.toLocaleString()}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  );
}

function BarRow({ label, value, total, colorClass }: { label: string; value: number; total: number; colorClass: string }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="w-36 text-xs text-slate-400 truncate shrink-0">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-slate-700 overflow-hidden">
        <div className={`h-full rounded-full transition-all ${colorClass}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-xs text-slate-500 text-right shrink-0">{value}</span>
    </div>
  );
}

const dateInputClass =
  'bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50';

// ── Tab: Summary Report ───────────────────────────────────────────────────────

function SummaryTab() {
  const [startDate, setStartDate] = useState(sevenDaysAgoStr());
  const [endDate, setEndDate] = useState(todayStr());
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetchError, setFetchError] = useState(false);
  const [hasGenerated, setHasGenerated] = useState(false);

  async function generateReport() {
    setLoading(true);
    setFetchError(false);
    try {
      const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
      const res = await apiFetch(`${API_BASE}/api/reports/summary?${params}`);
      if (!res.ok) throw new Error('Response not OK');
      const data: ReportData = await res.json();
      setReport(data);
      setHasGenerated(true);
    } catch {
      setFetchError(true);
      setReport(null);
    } finally {
      setLoading(false);
    }
  }

  const total = report?.total_requests ?? 0;

  return (
    <div className="space-y-5">
      {/* Date range picker */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-slate-200 mb-4">Select date range</h2>
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-400">Start date</label>
            <input type="date" value={startDate} max={endDate} onChange={(e) => setStartDate(e.target.value)} className={dateInputClass} />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-400">End date</label>
            <input type="date" value={endDate} min={startDate} max={todayStr()} onChange={(e) => setEndDate(e.target.value)} className={dateInputClass} />
          </div>
          <button
            onClick={generateReport}
            disabled={loading}
            className="flex items-center gap-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 px-5 py-2 text-xs font-semibold text-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {loading ? <><Spinner className="w-3.5 h-3.5" />Generating…</> : 'Generate Report'}
          </button>
          {report && (
            <button
              onClick={() => exportCSV(report)}
              className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-medium text-slate-200 hover:bg-slate-700 transition"
            >
              <ArrowDownTrayIcon className="w-3.5 h-3.5" />
              Export CSV
            </button>
          )}
        </div>
      </div>

      {fetchError && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-400/5 px-4 py-3 text-xs text-amber-400">
          Backend unavailable — start the CyberOracle backend to generate reports.
        </div>
      )}

      {!hasGenerated && !loading && !fetchError && (
        <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/50 px-4 py-10 text-center text-sm text-slate-500">
          Select a date range and click Generate Report to see statistics.
        </div>
      )}

      {report && (
        <>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-cyan-400/10 border border-cyan-500/30 px-3 py-1 text-xs font-medium text-cyan-400">
              {report.period.start} → {report.period.end}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Requests" value={total} />
            <StatCard label="Blocked" value={report.policy_decisions.blocked} sub={total > 0 ? `${Math.round((report.policy_decisions.blocked / total) * 100)}% of total` : undefined} color="text-red-400" />
            <StatCard label="Redacted" value={report.policy_decisions.redacted} sub={total > 0 ? `${Math.round((report.policy_decisions.redacted / total) * 100)}% of total` : undefined} color="text-amber-400" />
            <StatCard label="Allowed" value={report.policy_decisions.allowed} sub={total > 0 ? `${Math.round((report.policy_decisions.allowed / total) * 100)}% of total` : undefined} color="text-emerald-400" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h2 className="text-sm font-semibold text-slate-200 mb-4">Severity breakdown</h2>
              <div className="space-y-3">
                <BarRow label="High" value={report.severity.high} total={total} colorClass="bg-red-400" />
                <BarRow label="Medium" value={report.severity.medium} total={total} colorClass="bg-amber-400" />
                <BarRow label="Low" value={report.severity.low} total={total} colorClass="bg-blue-400" />
              </div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h2 className="text-sm font-semibold text-slate-200 mb-4">Policy decisions</h2>
              {report.decision_breakdown.length === 0 ? (
                <p className="text-xs text-slate-500">No decisions recorded.</p>
              ) : (
                <div className="space-y-2">
                  {report.decision_breakdown.map((row) => (
                    <div key={row.decision} className="flex items-center justify-between">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${decisionColor(row.decision)}`}>
                        {row.decision.charAt(0).toUpperCase() + row.decision.slice(1)}
                      </span>
                      <div className="flex items-center gap-3">
                        <div className="w-32 h-2 rounded-full bg-slate-700 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${row.decision === 'block' ? 'bg-red-400' : row.decision === 'redact' ? 'bg-amber-400' : 'bg-emerald-400'}`}
                            style={{ width: total > 0 ? `${Math.round((row.count / total) * 100)}%` : '0%' }}
                          />
                        </div>
                        <span className="text-xs text-slate-400 w-8 text-right">{row.count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h2 className="text-sm font-semibold text-slate-200 mb-4">Event types</h2>
              {report.event_type_breakdown.length === 0 ? (
                <p className="text-xs text-slate-500">No events recorded.</p>
              ) : (
                <div className="space-y-3">
                  {report.event_type_breakdown.map((row) => (
                    <BarRow key={row.event_type} label={row.event_type} value={row.count} total={total} colorClass="bg-cyan-400" />
                  ))}
                </div>
              )}
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h2 className="text-sm font-semibold text-slate-200 mb-4">Top endpoints</h2>
              {report.top_endpoints.length === 0 ? (
                <p className="text-xs text-slate-500">No endpoint data.</p>
              ) : (
                <div className="space-y-3">
                  {report.top_endpoints.map((row) => (
                    <BarRow key={row.endpoint} label={row.endpoint} value={row.count} total={total} colorClass="bg-violet-400" />
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ── Tab: Threat Analysis ──────────────────────────────────────────────────────

const WINDOW_OPTIONS = [
  { label: 'Last 1h', value: 1 },
  { label: 'Last 6h', value: 6 },
  { label: 'Last 24h', value: 24 },
];

function ThreatAnalysisTab() {
  const [windowHours, setWindowHours] = useState(1);
  const [report, setReport] = useState<RemediationReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetchError, setFetchError] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);

  async function runAnalysis() {
    setLoading(true);
    setFetchError(false);
    setExpanded(null);
    try {
      const res = await apiFetch(`${API_BASE}/api/reports/remediation?window_hours=${windowHours}`);
      if (!res.ok) throw new Error('Response not OK');
      setReport(await res.json());
    } catch {
      setFetchError(true);
      setReport(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-5">
      {/* Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-slate-200 mb-1">Threat Analysis</h2>
        <p className="text-xs text-slate-400 mb-4">
          Correlates log patterns to detect brute-force, DLP bypass probes, and risk clusters.
          Alerts are automatically fired for critical findings.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex rounded-lg overflow-hidden border border-slate-700">
            {WINDOW_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setWindowHours(opt.value)}
                className={`px-3 py-2 text-xs font-medium transition ${
                  windowHours === opt.value
                    ? 'bg-cyan-500 text-slate-900'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <button
            onClick={runAnalysis}
            disabled={loading}
            className="flex items-center gap-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 px-5 py-2 text-xs font-semibold text-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {loading ? <><Spinner className="w-3.5 h-3.5" />Analyzing…</> : 'Run Analysis'}
          </button>
        </div>
      </div>

      {fetchError && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-400/5 px-4 py-3 text-xs text-amber-400">
          Backend unavailable — start the CyberOracle backend to run threat analysis.
        </div>
      )}

      {!report && !loading && !fetchError && (
        <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/50 px-4 py-10 text-center text-sm text-slate-500">
          Select a time window and click Run Analysis to detect threats.
        </div>
      )}

      {report && (
        <>
          {/* Status banner */}
          <div className={`rounded-xl border px-5 py-4 flex items-start gap-3 ${
            report.status === 'CLEAN'
              ? 'border-emerald-500/20 bg-emerald-400/5'
              : report.overall_severity === 'critical'
              ? 'border-red-500/20 bg-red-400/5'
              : 'border-amber-500/20 bg-amber-400/5'
          }`}>
            <ShieldExclamationIcon className={`w-5 h-5 mt-0.5 shrink-0 ${
              report.status === 'CLEAN' ? 'text-emerald-400' : report.overall_severity === 'critical' ? 'text-red-400' : 'text-amber-400'
            }`} />
            <div>
              <p className={`text-sm font-semibold ${
                report.status === 'CLEAN' ? 'text-emerald-400' : report.overall_severity === 'critical' ? 'text-red-400' : 'text-amber-400'
              }`}>
                {report.status === 'CLEAN' ? 'No Threats Detected' : `${report.total_findings} Threat(s) Detected`}
              </p>
              <p className="text-xs text-slate-400 mt-0.5">{report.summary}</p>
              <p className="text-[10px] text-slate-500 mt-1">
                Analysis window: {report.analysis_window_hours}h — generated {new Date(report.generated_at).toLocaleString()}
              </p>
            </div>
          </div>

          {/* Finding cards */}
          {report.findings.length > 0 && (
            <div className="space-y-3">
              {report.findings.map((finding, idx) => {
                const key = `${finding.threat_type}-${idx}`;
                const isOpen = expanded === key;
                return (
                  <div key={key} className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <button
                      onClick={() => setExpanded(isOpen ? null : key)}
                      className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-slate-800 transition"
                    >
                      <div className="flex items-center gap-3">
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${severityBadge(finding.severity)}`}>
                          {finding.severity.toUpperCase()}
                        </span>
                        <div>
                          <p className="text-xs font-semibold text-slate-200">{finding.threat_type.replace(/_/g, ' ')}</p>
                          <p className="text-xs text-slate-400 mt-0.5">{finding.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 shrink-0 ml-4">
                        <span className="text-[10px] text-slate-500">Source: {finding.source}</span>
                        <span className="text-[10px] bg-slate-800 border border-slate-700 rounded px-2 py-0.5 text-slate-400">
                          {finding.affected_count} events
                        </span>
                        <ArrowPathIcon className={`w-3.5 h-3.5 text-slate-500 transition-transform ${isOpen ? 'rotate-90' : ''}`} />
                      </div>
                    </button>

                    {isOpen && (
                      <div className="border-t border-slate-800 px-5 py-4 space-y-3">
                        <div>
                          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">Recommendation</p>
                          <p className="text-xs text-slate-300">{finding.recommendation}</p>
                        </div>
                        <div>
                          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">Remediation Steps</p>
                          <ol className="space-y-1.5 list-none">
                            {finding.remediation_steps.map((step, i) => (
                              <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                                <span className="shrink-0 w-4 h-4 rounded-full bg-cyan-400/10 border border-cyan-500/20 text-cyan-400 text-[9px] font-bold flex items-center justify-center mt-0.5">
                                  {i + 1}
                                </span>
                                {step}
                              </li>
                            ))}
                          </ol>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Tab: DB Audit ─────────────────────────────────────────────────────────────

function DbAuditTab() {
  const [audit, setAudit] = useState<DbAudit | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetchError, setFetchError] = useState(false);

  async function loadAudit() {
    setLoading(true);
    setFetchError(false);
    try {
      const res = await apiFetch(`${API_BASE}/api/reports/db-audit`);
      if (!res.ok) throw new Error('Response not OK');
      setAudit(await res.json());
    } catch {
      setFetchError(true);
      setAudit(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAudit();
  }, []);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-slate-200">Database Security Audit</h2>
          <p className="text-xs text-slate-400 mt-0.5">Log volume, encryption status, and 24h policy activity.</p>
        </div>
        <button
          onClick={loadAudit}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-medium text-slate-200 hover:bg-slate-700 disabled:opacity-50 transition"
        >
          <ArrowPathIcon className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          Refresh
        </button>
      </div>

      {fetchError && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-400/5 px-4 py-3 text-xs text-amber-400">
          Backend unavailable — start the CyberOracle backend to view the DB audit.
        </div>
      )}

      {loading && !audit && (
        <div className="flex justify-center py-10">
          <Spinner className="w-6 h-6" />
        </div>
      )}

      {audit && (
        <>
          {/* Top-level stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Log Entries" value={audit.total_log_entries} />
            <StatCard label="High Severity" value={audit.severity_breakdown.high} color="text-red-400" />
            <StatCard label="Medium Severity" value={audit.severity_breakdown.medium} color="text-amber-400" />
            <StatCard label="High-Risk Events (24h)" value={audit.high_risk_events_24h} color="text-red-400" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Policy decisions 24h */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-slate-200 mb-4">Policy Decisions (24h)</h3>
              <div className="space-y-3">
                {(['block', 'redact', 'allow'] as const).map((d) => {
                  const total = audit.policy_decisions_24h.allow + audit.policy_decisions_24h.redact + audit.policy_decisions_24h.block;
                  return (
                    <BarRow
                      key={d}
                      label={d.charAt(0).toUpperCase() + d.slice(1)}
                      value={audit.policy_decisions_24h[d]}
                      total={total}
                      colorClass={d === 'block' ? 'bg-red-400' : d === 'redact' ? 'bg-amber-400' : 'bg-emerald-400'}
                    />
                  );
                })}
              </div>
            </div>

            {/* DB security status */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-slate-200 mb-4">Database Security</h3>
              <div className="space-y-3">
                <StatusRow
                  label="Encryption at Rest"
                  active={audit.database_security.encryption_enabled}
                  trueText="Enabled (Fernet AES-128)"
                  falseText="Disabled"
                />
                <StatusRow
                  label="Audit Trail"
                  active={audit.database_security.audit_trail_active}
                  trueText="Active"
                  falseText="Inactive"
                />
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Encrypted fields</span>
                  <span className="text-xs text-slate-300 font-mono">
                    {audit.database_security.encrypted_fields.length > 0
                      ? audit.database_security.encrypted_fields.join(', ')
                      : 'none'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Generated at</span>
                  <span className="text-xs text-slate-500">
                    {new Date(audit.audit_generated_at).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Severity breakdown bar */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-slate-200 mb-4">All-Time Severity Breakdown</h3>
            <div className="space-y-3">
              <BarRow label="High" value={audit.severity_breakdown.high} total={audit.total_log_entries} colorClass="bg-red-400" />
              <BarRow label="Medium" value={audit.severity_breakdown.medium} total={audit.total_log_entries} colorClass="bg-amber-400" />
              <BarRow label="Low" value={audit.severity_breakdown.low} total={audit.total_log_entries} colorClass="bg-blue-400" />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function StatusRow({ label, active, trueText, falseText }: { label: string; active: boolean; trueText: string; falseText: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-slate-400">{label}</span>
      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${active ? 'bg-emerald-400/10 text-emerald-400' : 'bg-red-400/10 text-red-400'}`}>
        {active ? trueText : falseText}
      </span>
    </div>
  );
}

// ── Root component ────────────────────────────────────────────────────────────

type TabId = 'summary' | 'threats' | 'db-audit';

const TABS: { id: TabId; label: string; icon: React.ComponentType<React.SVGProps<SVGSVGElement>> }[] = [
  { id: 'summary', label: 'Summary Report', icon: ArrowDownTrayIcon },
  { id: 'threats', label: 'Threat Analysis', icon: ShieldExclamationIcon },
  { id: 'db-audit', label: 'DB Audit', icon: CircleStackIcon },
];

const ReportsPanel: React.FC = () => {
  const [tab, setTab] = useState<TabId>('summary');

  return (
    <div className="mt-4 space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">Reports</h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Security summaries, threat analysis, and database audit for PSPR8 monitoring.
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-slate-800">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium border-b-2 transition ${
              tab === id
                ? 'border-cyan-400 text-cyan-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'summary' && <SummaryTab />}
      {tab === 'threats' && <ThreatAnalysisTab />}
      {tab === 'db-audit' && <DbAuditTab />}
    </div>
  );
};

export default ReportsPanel;
