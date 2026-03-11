'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../lib/auth';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type AlertItem = {
  id: string;
  type: string;
  severity: string;
  message: string;
  timestamp: string;
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function relativeTime(iso: string): string {
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

function severityBadgeClass(s: string): string {
  const v = s.toLowerCase();
  if (v === 'high') return 'bg-red-100 text-red-700 border-red-200';
  if (v === 'medium') return 'bg-yellow-100 text-yellow-800 border-yellow-200';
  if (v === 'low') return 'bg-blue-100 text-blue-700 border-blue-200';
  return 'bg-slate-100 text-slate-600 border-slate-200';
}

function severityCardBorder(s: string): string {
  const v = s.toLowerCase();
  if (v === 'high') return 'border-l-4 border-l-red-400';
  if (v === 'medium') return 'border-l-4 border-l-yellow-400';
  if (v === 'low') return 'border-l-4 border-l-blue-400';
  return 'border-l-4 border-l-slate-300';
}

function severityIcon(s: string): string {
  const v = s.toLowerCase();
  if (v === 'high') return '⚠';
  if (v === 'medium') return '◆';
  if (v === 'low') return '●';
  return '○';
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const AlertsPanel: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [severityFilter, setSeverityFilter] = useState('');
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    setFetchError(false);
    try {
      const res = await apiFetch(`${API_BASE}/api/alerts/recent`);
      if (!res.ok) throw new Error('Response not OK');
      const data = await res.json();
      setAlerts(
        (data.alerts ?? []).map((a: Record<string, unknown>) => ({
          id: String(a.id ?? ''),
          type: String(a.type ?? 'Security Event'),
          severity: String(a.severity ?? 'info'),
          message: String(a.message ?? ''),
          timestamp: String(a.timestamp ?? ''),
        })),
      );
      setLastRefreshed(new Date());
      setDismissed(new Set()); // clear dismissals on refresh
    } catch {
      setFetchError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  function dismiss(id: string) {
    setDismissed((prev) => new Set([...prev, id]));
  }

  function dismissAll() {
    setDismissed(new Set(visible.map((a) => a.id)));
  }

  const visible = alerts.filter(
    (a) =>
      !dismissed.has(a.id) &&
      (severityFilter === '' || a.severity.toLowerCase() === severityFilter),
  );

  // Stats from full (non-dismissed) list
  const active = alerts.filter((a) => !dismissed.has(a.id));
  const highCount = active.filter((a) => a.severity.toLowerCase() === 'high').length;
  const medCount = active.filter((a) => a.severity.toLowerCase() === 'medium').length;
  const lowCount = active.filter((a) => a.severity.toLowerCase() === 'low').length;

  return (
    <div className="mt-4 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Alerts</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Recent high-risk events detected by CyberOracle.
            {lastRefreshed && (
              <span className="ml-2 text-slate-400">
                Last refreshed {relativeTime(lastRefreshed.toISOString())}
              </span>
            )}
          </p>
        </div>
        <button
          onClick={fetchAlerts}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
        >
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {/* Error banner */}
      {fetchError && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-700">
          Backend unavailable — start the CyberOracle backend to see live
          alerts.
        </div>
      )}

      {/* Stats strip */}
      {!loading && !fetchError && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 text-center">
            <p className="text-2xl font-semibold text-red-600">{highCount}</p>
            <p className="text-xs text-slate-500 mt-0.5">High severity</p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 text-center">
            <p className="text-2xl font-semibold text-yellow-600">{medCount}</p>
            <p className="text-xs text-slate-500 mt-0.5">Medium severity</p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 text-center">
            <p className="text-2xl font-semibold text-blue-600">{lowCount}</p>
            <p className="text-xs text-slate-500 mt-0.5">Low severity</p>
          </div>
        </div>
      )}

      {/* Filter + dismiss-all bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-wrap items-center gap-3">
        <span className="text-xs font-medium text-slate-500">Filter:</span>
        {['', 'high', 'medium', 'low'].map((v) => (
          <button
            key={v}
            onClick={() => setSeverityFilter(v)}
            className={
              'rounded-lg border px-3 py-1.5 text-xs font-medium transition ' +
              (severityFilter === v
                ? 'bg-sky-50 border-sky-200 text-sky-700'
                : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50')
            }
          >
            {v === '' ? 'All' : v.charAt(0).toUpperCase() + v.slice(1)}
          </button>
        ))}

        {visible.length > 0 && (
          <button
            onClick={dismissAll}
            className="ml-auto rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-500 hover:bg-slate-50 transition"
          >
            Dismiss all
          </button>
        )}
      </div>

      {/* Alert feed */}
      <div className="space-y-3">
        {loading ? (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm px-6 py-10 text-center text-sm text-slate-400">
            Loading alerts…
          </div>
        ) : visible.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm px-6 py-10 text-center">
            <p className="text-sm text-slate-500">
              {dismissed.size > 0
                ? 'All alerts have been dismissed.'
                : severityFilter
                  ? `No ${severityFilter} severity alerts.`
                  : 'No alerts to display.'}
            </p>
            {dismissed.size > 0 && (
              <button
                onClick={fetchAlerts}
                className="mt-3 text-xs text-sky-600 hover:underline"
              >
                Refresh to reload
              </button>
            )}
          </div>
        ) : (
          visible.map((alert) => (
            <div
              key={alert.id}
              className={`bg-white rounded-xl border border-slate-200 shadow-sm p-4 ${severityCardBorder(alert.severity)}`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 min-w-0">
                  {/* Icon */}
                  <span
                    className={`mt-0.5 text-base shrink-0 ${
                      alert.severity.toLowerCase() === 'high'
                        ? 'text-red-500'
                        : alert.severity.toLowerCase() === 'medium'
                          ? 'text-yellow-500'
                          : 'text-blue-400'
                    }`}
                  >
                    {severityIcon(alert.severity)}
                  </span>

                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className="text-xs font-semibold text-slate-800">
                        {alert.type}
                      </span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${severityBadgeClass(alert.severity)}`}
                      >
                        {alert.severity.charAt(0).toUpperCase() +
                          alert.severity.slice(1)}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 break-words">
                      {alert.message}
                    </p>
                    <p className="text-[10px] text-slate-400 mt-1.5">
                      {relativeTime(alert.timestamp)}
                    </p>
                  </div>
                </div>

                {/* Dismiss button */}
                <button
                  onClick={() => dismiss(alert.id)}
                  title="Dismiss alert"
                  className="shrink-0 rounded-lg border border-slate-200 px-2.5 py-1 text-[10px] text-slate-400 hover:bg-slate-50 hover:text-slate-600 transition"
                >
                  Dismiss
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Note about dismiss scope */}
      {visible.length > 0 && (
        <p className="text-[10px] text-slate-400 text-right">
          Dismiss is session-only — alerts reload on next refresh.
        </p>
      )}
    </div>
  );
};

export default AlertsPanel;
