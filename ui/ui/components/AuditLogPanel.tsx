'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../lib/auth';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

const PAGE_SIZE = 20;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

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
};

type Filters = {
  severity: string;
  event_type: string;
  policy_decision: string;
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

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
  if (!s) return 'bg-slate-100 text-slate-500';
  const v = s.toLowerCase();
  if (v === 'high') return 'bg-red-100 text-red-700';
  if (v === 'medium') return 'bg-yellow-100 text-yellow-800';
  if (v === 'low') return 'bg-blue-100 text-blue-700';
  return 'bg-slate-100 text-slate-500';
}

function policyBadge(p: string | null): string {
  if (!p) return 'bg-slate-100 text-slate-500';
  const v = p.toLowerCase();
  if (v === 'block') return 'bg-red-100 text-red-700';
  if (v === 'redact') return 'bg-amber-100 text-amber-700';
  if (v === 'allow') return 'bg-green-100 text-green-700';
  return 'bg-slate-100 text-slate-500';
}

function cap(s: string | null): string {
  if (!s) return '—';
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function exportCSV(logs: LogEntry[]) {
  const headers = [
    'ID',
    'Timestamp',
    'Endpoint',
    'Method',
    'Status',
    'Event Type',
    'Severity',
    'Risk Score',
    'Policy Decision',
    'Source',
    'Message',
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
    // strip commas from message to keep CSV valid
    (e.message ?? '').replace(/,/g, ' '),
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

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const AuditLogPanel: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [page, setPage] = useState(0); // 0-indexed
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

  const firstRecord = page * PAGE_SIZE + 1;
  const lastRecord = page * PAGE_SIZE + logs.length;
  const activeFilters = Object.values(filters).some((v) => v !== '');

  return (
    <div className="mt-4 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Audit Log</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Full searchable trail of all AI requests, DLP decisions, and policy
            actions.
          </p>
        </div>
        <button
          onClick={() => exportCSV(logs)}
          disabled={logs.length === 0}
          className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
        >
          Export CSV
        </button>
      </div>

      {/* Error banner */}
      {fetchError && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-700">
          Backend unavailable — start the CyberOracle backend to see audit logs.
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-xs font-medium text-slate-500">Filter:</span>

          <select
            value={filters.severity}
            onChange={(e) => applyFilter('severity', e.target.value)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-sky-300"
          >
            <option value="">All severities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>

          <select
            value={filters.event_type}
            onChange={(e) => applyFilter('event_type', e.target.value)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-sky-300"
          >
            <option value="">All event types</option>
            <option value="ai_query">AI Query</option>
            <option value="ai_query_blocked">AI Query Blocked</option>
            <option value="dlp_alert">DLP Alert</option>
            <option value="auth_failure">Auth Failure</option>
            <option value="rate_limit">Rate Limit</option>
          </select>

          <select
            value={filters.policy_decision}
            onChange={(e) => applyFilter('policy_decision', e.target.value)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-sky-300"
          >
            <option value="">All decisions</option>
            <option value="allow">Allow</option>
            <option value="redact">Redact</option>
            <option value="block">Block</option>
          </select>

          {activeFilters && (
            <button
              onClick={clearFilters}
              className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-500 hover:bg-slate-50 transition"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50 text-left">
                <th className="px-4 py-3 font-semibold text-slate-600 whitespace-nowrap">Time</th>
                <th className="px-4 py-3 font-semibold text-slate-600 whitespace-nowrap">Event Type</th>
                <th className="px-4 py-3 font-semibold text-slate-600 whitespace-nowrap">Endpoint</th>
                <th className="px-4 py-3 font-semibold text-slate-600 whitespace-nowrap">Method</th>
                <th className="px-4 py-3 font-semibold text-slate-600 whitespace-nowrap">Status</th>
                <th className="px-4 py-3 font-semibold text-slate-600 whitespace-nowrap">Severity</th>
                <th className="px-4 py-3 font-semibold text-slate-600 whitespace-nowrap">Risk</th>
                <th className="px-4 py-3 font-semibold text-slate-600 whitespace-nowrap">Decision</th>
                <th className="px-4 py-3 font-semibold text-slate-600">Message</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-4 py-10 text-center text-slate-400">
                    Loading logs…
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-10 text-center text-slate-400">
                    {activeFilters ? 'No logs match the selected filters.' : 'No audit logs found.'}
                  </td>
                </tr>
              ) : (
                logs.map((entry) => (
                  <tr
                    key={entry.id}
                    className="border-b border-slate-50 hover:bg-slate-50 transition"
                  >
                    <td className="px-4 py-2.5 whitespace-nowrap text-slate-500">
                      {relativeTime(entry.created_at)}
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap text-slate-700">
                      {entry.event_type ?? '—'}
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap font-mono text-slate-600 max-w-[160px] truncate">
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
                            ? 'bg-red-100 text-red-700'
                            : entry.status_code >= 400
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-green-100 text-green-700')
                        }
                      >
                        {entry.status_code}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap">
                      {entry.severity ? (
                        <span
                          className={`px-2 py-0.5 rounded-full font-semibold ${severityBadge(entry.severity)}`}
                        >
                          {cap(entry.severity)}
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap text-slate-600">
                      {entry.risk_score != null
                        ? entry.risk_score.toFixed(2)
                        : '—'}
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap">
                      {entry.policy_decision ? (
                        <span
                          className={`px-2 py-0.5 rounded-full font-semibold ${policyBadge(entry.policy_decision)}`}
                        >
                          {cap(entry.policy_decision)}
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-slate-500 max-w-[220px] truncate">
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
          <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3">
            <span className="text-xs text-slate-500">
              Showing {firstRecord}–{lastRecord}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >
                Previous
              </button>
              <span className="text-xs text-slate-500">Page {page + 1}</span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={!hasMore}
                className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditLogPanel;
