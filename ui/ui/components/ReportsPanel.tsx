'use client';

import React, { useState } from 'react';
import { apiFetch } from '../lib/auth';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ReportData = {
  period: { start: string; end: string };
  total_requests: number;
  policy_decisions: { blocked: number; redacted: number; allowed: number };
  severity: { high: number; medium: number; low: number };
  event_type_breakdown: { event_type: string; count: number }[];
  decision_breakdown: { decision: string; count: number }[];
  top_endpoints: { endpoint: string; count: number }[];
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function sevenDaysAgoStr() {
  const d = new Date();
  d.setDate(d.getDate() - 7);
  return d.toISOString().slice(0, 10);
}

function decisionColor(d: string): string {
  const v = d.toLowerCase();
  if (v === 'block') return 'bg-red-100 text-red-700';
  if (v === 'redact') return 'bg-amber-100 text-amber-700';
  if (v === 'allow') return 'bg-green-100 text-green-700';
  return 'bg-slate-100 text-slate-600';
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
  data.event_type_breakdown.forEach((r) =>
    lines.push([r.event_type, String(r.count)]),
  );
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

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatCard({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: number;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
      <p className="text-xs font-medium text-slate-500 mb-1">{label}</p>
      <p className={`text-2xl font-semibold ${color ?? 'text-slate-900'}`}>
        {value.toLocaleString()}
      </p>
      {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
    </div>
  );
}

function BarRow({
  label,
  value,
  total,
  colorClass,
}: {
  label: string;
  value: number;
  total: number;
  colorClass: string;
}) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="w-36 text-xs text-slate-600 truncate shrink-0">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${colorClass}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-8 text-xs text-slate-500 text-right shrink-0">{value}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

const ReportsPanel: React.FC = () => {
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
    <div className="mt-4 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Reports</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Generate aggregated security summaries for any date range.
          </p>
        </div>
        {report && (
          <button
            onClick={() => exportCSV(report)}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50 transition"
          >
            Export CSV
          </button>
        )}
      </div>

      {/* Date range + generate */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-800 mb-4">
          Select date range
        </h2>
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500">Start date</label>
            <input
              type="date"
              value={startDate}
              max={endDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-300"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500">End date</label>
            <input
              type="date"
              value={endDate}
              min={startDate}
              max={todayStr()}
              onChange={(e) => setEndDate(e.target.value)}
              className="rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-300"
            />
          </div>
          <button
            onClick={generateReport}
            disabled={loading}
            className="rounded-lg bg-sky-600 px-5 py-2 text-xs font-semibold text-white hover:bg-sky-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {loading ? 'Generating…' : 'Generate Report'}
          </button>
        </div>
      </div>

      {/* Error */}
      {fetchError && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-700">
          Backend unavailable — start the CyberOracle backend to generate
          reports.
        </div>
      )}

      {/* Pre-generate placeholder */}
      {!hasGenerated && !loading && !fetchError && (
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-10 text-center text-sm text-slate-400">
          Select a date range and click Generate Report to see statistics.
        </div>
      )}

      {/* Results */}
      {report && (
        <>
          {/* Period badge */}
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-sky-50 border border-sky-200 px-3 py-1 text-xs font-medium text-sky-700">
              {report.period.start} → {report.period.end}
            </span>
          </div>

          {/* Summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Requests" value={total} />
            <StatCard
              label="Blocked"
              value={report.policy_decisions.blocked}
              sub={total > 0 ? `${Math.round((report.policy_decisions.blocked / total) * 100)}% of total` : undefined}
              color="text-red-600"
            />
            <StatCard
              label="Redacted"
              value={report.policy_decisions.redacted}
              sub={total > 0 ? `${Math.round((report.policy_decisions.redacted / total) * 100)}% of total` : undefined}
              color="text-amber-600"
            />
            <StatCard
              label="Allowed"
              value={report.policy_decisions.allowed}
              sub={total > 0 ? `${Math.round((report.policy_decisions.allowed / total) * 100)}% of total` : undefined}
              color="text-green-600"
            />
          </div>

          {/* Middle row: severity + policy decisions */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Severity */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
              <h2 className="text-sm font-semibold text-slate-800 mb-4">
                Severity breakdown
              </h2>
              <div className="space-y-3">
                <BarRow
                  label="High"
                  value={report.severity.high}
                  total={total}
                  colorClass="bg-red-400"
                />
                <BarRow
                  label="Medium"
                  value={report.severity.medium}
                  total={total}
                  colorClass="bg-yellow-400"
                />
                <BarRow
                  label="Low"
                  value={report.severity.low}
                  total={total}
                  colorClass="bg-blue-400"
                />
              </div>
            </div>

            {/* Policy decisions */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
              <h2 className="text-sm font-semibold text-slate-800 mb-4">
                Policy decisions
              </h2>
              {report.decision_breakdown.length === 0 ? (
                <p className="text-xs text-slate-400">No decisions recorded.</p>
              ) : (
                <div className="space-y-2">
                  {report.decision_breakdown.map((row) => (
                    <div key={row.decision} className="flex items-center justify-between">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full font-semibold ${decisionColor(row.decision)}`}
                      >
                        {row.decision.charAt(0).toUpperCase() + row.decision.slice(1)}
                      </span>
                      <div className="flex items-center gap-3">
                        <div className="w-32 h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              row.decision === 'block'
                                ? 'bg-red-400'
                                : row.decision === 'redact'
                                  ? 'bg-amber-400'
                                  : 'bg-green-400'
                            }`}
                            style={{
                              width: total > 0
                                ? `${Math.round((row.count / total) * 100)}%`
                                : '0%',
                            }}
                          />
                        </div>
                        <span className="text-xs text-slate-600 w-8 text-right">
                          {row.count}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Bottom row: event types + top endpoints */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Event type breakdown */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
              <h2 className="text-sm font-semibold text-slate-800 mb-4">
                Event types
              </h2>
              {report.event_type_breakdown.length === 0 ? (
                <p className="text-xs text-slate-400">No events recorded.</p>
              ) : (
                <div className="space-y-3">
                  {report.event_type_breakdown.map((row) => (
                    <BarRow
                      key={row.event_type}
                      label={row.event_type}
                      value={row.count}
                      total={total}
                      colorClass="bg-sky-400"
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Top endpoints */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
              <h2 className="text-sm font-semibold text-slate-800 mb-4">
                Top endpoints
              </h2>
              {report.top_endpoints.length === 0 ? (
                <p className="text-xs text-slate-400">No endpoint data.</p>
              ) : (
                <div className="space-y-3">
                  {report.top_endpoints.map((row) => (
                    <BarRow
                      key={row.endpoint}
                      label={row.endpoint}
                      value={row.count}
                      total={total}
                      colorClass="bg-violet-400"
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ReportsPanel;
