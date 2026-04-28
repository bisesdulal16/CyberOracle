'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../lib/auth';
import {
  ArrowPathIcon,
  ArrowDownTrayIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  FunnelIcon,
  ShieldCheckIcon,
  ShieldExclamationIcon,
} from '@heroicons/react/24/outline';

// Fixed: use the same env var as the rest of the app
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8003';

const PAGE_SIZE = 20;

type LogEntry = {
  id: number;
  endpoint: string;
  method: string;
  status_code: number;
  event_type: string | null;
  severity: string | null;
  risk_score: number | null;
  source: string | null;
  policy_decision: string | null;
  message: string | null;
  created_at: string | null;
  // null = pre-dates integrity hashing, true = verified, false = tampered
  integrity_verified: boolean | null;
};

type Filters = {
  severity: string;
  event_type: string;
  policy_decision: string;
};

function Spinner({ className }: { className?: string }) {
  return <ArrowPathIcon className={`animate-spin text-cyan-400 ${className ?? 'w-5 h-5'}`} />;
}

function relativeTime(iso: string | null): string {
  if (!iso) return '—';
  const ms = Date.now() - new Date(iso).getTime();
  if (isNaN(ms) || ms < 0) return iso;
  const minutes = Math.floor(ms / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function severityBadge(s: string | null): string {
  if (!s) return 'bg-slate-800 text-slate-500';
  const v = s.toLowerCase();
  if (v === 'high') return 'bg-red-400/10 text-red-400 border border-red-500/20';
  if (v === 'medium') return 'bg-amber-400/10 text-amber-400 border border-amber-500/20';
  if (v === 'low') return 'bg-blue-400/10 text-blue-400 border border-blue-500/20';
  return 'bg-slate-800 text-slate-500';
}

function policyBadge(p: string | null): string {
  if (!p) return 'bg-slate-800 text-slate-500';
  const v = p.toLowerCase();
  if (v === 'block') return 'bg-red-400/10 text-red-400 border border-red-500/20';
  if (v === 'redact') return 'bg-amber-400/10 text-amber-400 border border-amber-500/20';
  if (v === 'allow') return 'bg-emerald-400/10 text-emerald-400 border border-emerald-500/20';
  return 'bg-slate-800 text-slate-500';
}

function cap(s: string | null): string {
  if (!s) return '—';
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function IntegrityBadge({ verified }: { verified: boolean | null }) {
  // null = old entry, no hash stored yet — show nothing
  if (verified === null) return <span className="text-slate-600">—</span>;

  if (verified) {
    return (
      <span
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold bg-emerald-400/10 text-emerald-400 border border-emerald-500/20"
        title="Log integrity verified — entry has not been tampered with"
      >
        <ShieldCheckIcon className="w-3 h-3" />
        OK
      </span>
    );
  }

  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold bg-red-400/10 text-red-400 border border-red-500/20"
      title="WARNING: Log integrity check failed — this entry may have been tampered with"
    >
      <ShieldExclamationIcon className="w-3 h-3" />
      TAMPERED
    </span>
  );
}

function exportCSV(logs: LogEntry[]) {
  const headers = [
    'ID', 'Timestamp', 'Endpoint', 'Method', 'Status',
    'Event Type', 'Severity', 'Risk Score', 'Policy Decision', 'Source', 'Message', 'Integrity',
  ];
  const rows = logs.map((e) => [
    e.id,
    e.created_at ?? '',
    e.endpoint,
    e.method,
    e.status_code,
    e.event_type ?? '',
    e.severity ?? '',
    e.risk_score ?? '',
    e.policy_decision ?? '',
    e.source ?? '',
    (e.message ?? '').replace(/,/g, ' '),
    e.integrity_verified === null ? 'N/A' : e.integrity_verified ? 'Verified' : 'TAMPERED',
  ]);

  const csv = [headers, ...rows]
    .map((row) => row.map((v) => `"${v}"`).join(','))
    .join('\n');

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `cyberoracle-audit-log-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

const selectClass =
  'bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 placeholder:text-slate-500';

const AuditLogPanel: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [filters, setFilters] = useState<Filters>({
    severity: '',
    event_type: '',
    policy_decision: '',
  });

  const fetchLogs = useCallback(
    async (currentPage: number, currentFilters: Filters) => {
      setLoading(true);
      setFetchError(false);
      try {
        const params = new URLSearchParams({
          limit: String(PAGE_SIZE),
          offset: String(currentPage * PAGE_SIZE),
        });
        if (currentFilters.severity) params.set('severity', currentFilters.severity);
        if (currentFilters.event_type) params.set('event_type', currentFilters.event_type);
        if (currentFilters.policy_decision) params.set('policy_decision', currentFilters.policy_decision);

        const res = await apiFetch(`${API_BASE}/logs/list?${params.toString()}`);
        if (!res.ok) throw new Error('Response not OK');
        const data = await res.json();
        setLogs(data.logs ?? []);
        setHasMore((data.count ?? 0) === PAGE_SIZE);
      } catch {
        setFetchError(true);
        setLogs([]);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    fetchLogs(page, filters);
  }, [page, filters, fetchLogs]);

  function applyFilter(key: keyof Filters, value: string) {
    setPage(0);
    setFilters((prev) => ({ ...prev, [key]: value }));
  }

  function clearFilters() {
    setPage(0);
    setFilters({ severity: '', event_type: '', policy_decision: '' });
  }

  // Warn if any visible entries have failed integrity checks
  const tamperedCount = logs.filter((l) => l.integrity_verified === false).length;

  const firstRecord = page * PAGE_SIZE + 1;
  const lastRecord = page * PAGE_SIZE + logs.length;
  const activeFilters = Object.values(filters).some((v) => v !== '');

  return (
    <div className="mt-4 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">Audit Log</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Full searchable trail of all AI requests, DLP decisions, and policy
            actions.
          </p>
        </div>
        <button
          onClick={() => exportCSV(logs)}
          disabled={logs.length === 0}
          className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-medium text-slate-200 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
        >
          <ArrowDownTrayIcon className="w-3.5 h-3.5" />
          Export CSV
        </button>
      </div>

      {/* Tamper warning banner */}
      {tamperedCount > 0 && (
        <div className="flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3">
          <ShieldExclamationIcon className="w-5 h-5 text-red-400 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-400">
              Integrity warning — {tamperedCount} tampered {tamperedCount === 1 ? 'entry' : 'entries'} detected
            </p>
            <p className="text-xs text-red-400/70 mt-0.5">
              One or more log entries have failed their integrity check. These records may have been
              modified after storage. Escalate to an administrator immediately.
            </p>
          </div>
        </div>
      )}

      {/* Error banner */}
      {fetchError && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-400/5 px-4 py-3 text-xs text-amber-400">
          Backend unavailable — start the CyberOracle backend to see audit logs.
        </div>
      )}

      {/* Filters */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-medium text-slate-400">
            <FunnelIcon className="w-3.5 h-3.5" />
            Filter:
          </div>

          <select
            value={filters.severity}
            onChange={(e) => applyFilter('severity', e.target.value)}
            className={selectClass}
          >
            <option value="">All severities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>

          <select
            value={filters.event_type}
            onChange={(e) => applyFilter('event_type', e.target.value)}
            className={selectClass}
          >
            <option value="">All event types</option>
            <option value="ai_query">AI Query</option>
            <option value="ai_query_blocked">AI Query Blocked</option>
            <option value="dlp_alert">DLP Alert</option>
            <option value="document_sanitize">Document Sanitize</option>
            <option value="ai_query_model_error">Model Error</option>
          </select>

          <select
            value={filters.policy_decision}
            onChange={(e) => applyFilter('policy_decision', e.target.value)}
            className={selectClass}
          >
            <option value="">All decisions</option>
            <option value="allow">Allow</option>
            <option value="redact">Redact</option>
            <option value="block">Block</option>
          </select>

          {activeFilters && (
            <button
              onClick={clearFilters}
              className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-400 hover:bg-slate-700 hover:text-slate-200 transition"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-800 text-left">
                <th className="px-4 py-3 font-semibold text-slate-400 whitespace-nowrap">Time</th>
                <th className="px-4 py-3 font-semibold text-slate-400 whitespace-nowrap">Event Type</th>
                <th className="px-4 py-3 font-semibold text-slate-400 whitespace-nowrap">Endpoint</th>
                <th className="px-4 py-3 font-semibold text-slate-400 whitespace-nowrap">Method</th>
                <th className="px-4 py-3 font-semibold text-slate-400 whitespace-nowrap">Status</th>
                <th className="px-4 py-3 font-semibold text-slate-400 whitespace-nowrap">Severity</th>
                <th className="px-4 py-3 font-semibold text-slate-400 whitespace-nowrap">Risk</th>
                <th className="px-4 py-3 font-semibold text-slate-400 whitespace-nowrap">Decision</th>
                <th className="px-4 py-3 font-semibold text-slate-400 whitespace-nowrap">Integrity</th>
                <th className="px-4 py-3 font-semibold text-slate-400">Message</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={10} className="px-4 py-10 text-center">
                    <div className="flex justify-center">
                      <Spinner />
                    </div>
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-4 py-10 text-center text-slate-500">
                    {activeFilters ? 'No logs match the selected filters.' : 'No audit logs found.'}
                  </td>
                </tr>
              ) : (
                logs.map((entry) => (
                  <tr
                    key={entry.id}
                    className={`border-b border-slate-800 transition ${
                      entry.integrity_verified === false
                        ? 'bg-red-500/5 hover:bg-red-500/10'
                        : 'hover:bg-slate-800'
                    }`}
                  >
                    <td className="px-4 py-2.5 whitespace-nowrap text-slate-500" title={entry.created_at ?? ''}>
                      {relativeTime(entry.created_at)}
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap text-slate-300" title={entry.event_type ?? ''}>
                      {entry.event_type ?? '—'}
                    </td>
                    <td
                      className="px-4 py-2.5 whitespace-nowrap font-mono text-slate-400 max-w-[160px] truncate"
                      title={entry.endpoint}
                    >
                      {entry.endpoint}
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap text-slate-500 uppercase">
                      {entry.method}
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap">
                      <span
                        className={
                          'px-2 py-0.5 rounded-full font-semibold ' +
                          (entry.status_code >= 500
                            ? 'bg-red-400/10 text-red-400 border border-red-500/20'
                            : entry.status_code >= 400
                              ? 'bg-amber-400/10 text-amber-400 border border-amber-500/20'
                              : 'bg-emerald-400/10 text-emerald-400 border border-emerald-500/20')
                        }
                      >
                        {entry.status_code}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap">
                      {entry.severity ? (
                        <span className={`px-2 py-0.5 rounded-full font-semibold ${severityBadge(entry.severity)}`}>
                          {cap(entry.severity)}
                        </span>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap text-slate-400">
                      {entry.risk_score != null ? entry.risk_score.toFixed(2) : '—'}
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap">
                      {entry.policy_decision ? (
                        <span className={`px-2 py-0.5 rounded-full font-semibold ${policyBadge(entry.policy_decision)}`}>
                          {cap(entry.policy_decision)}
                        </span>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap">
                      <IntegrityBadge verified={entry.integrity_verified} />
                    </td>
                    <td
                      className="px-4 py-2.5 text-slate-500 max-w-[220px] truncate"
                      title={entry.message ?? ''}
                    >
                      {entry.message ?? '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!loading && logs.length > 0 && (
          <div className="flex items-center justify-between border-t border-slate-800 px-4 py-3">
            <span className="text-xs text-slate-500">
              Showing {firstRecord}–{lastRecord}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >
                <ChevronLeftIcon className="w-3.5 h-3.5" />
                Previous
              </button>
              <span className="text-xs text-slate-500">Page {page + 1}</span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={!hasMore}
                className="flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >
                Next
                <ChevronRightIcon className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditLogPanel;