'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, clearAuth, getRole, apiFetch } from '../lib/auth';
import SecureChatPanel from './SecureChatPanel';
import DocumentSanitizerPanel from './DocumentSanitizerPanel';
import CompliancePanel from './CompliancePanel';
import AuditLogPanel from './AuditLogPanel';
import AlertsPanel from './AlertsPanel';
import ReportsPanel from './ReportsPanel';
import Settings from './Settings';
import KnowledgeBasePanel from './KnowledgeBasePanel';
import {
  Squares2X2Icon,
  ChatBubbleLeftRightIcon,
  DocumentMagnifyingGlassIcon,
  CpuChipIcon,
  CircleStackIcon,
  BookOpenIcon,
  ShieldCheckIcon,
  BellAlertIcon,
  ClipboardDocumentListIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  ArrowRightStartOnRectangleIcon,
  ArrowTopRightOnSquareIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

type SummaryMetrics = {
  totalPrompts24h: number;
  blockedPrompts: number;
  redactedOutputs: number;
  highRiskEvents: number;
};

type ComplianceStatus = {
  complianceScore: number;
  compliantControls: number;
  totalControls: number;
};

type AlertItem = {
  id: string;
  type: string;
  severity: string;
  message: string;
  timestamp: string;
};

function Spinner({ className }: { className?: string }) {
  return <ArrowPathIcon className={`animate-spin text-cyan-400 ${className ?? 'w-5 h-5'}`} />;
}

function relativeTime(iso: string): string {
  const ms = Date.now() - new Date(iso).getTime();
  if (isNaN(ms) || ms < 0) return iso;
  const minutes = Math.floor(ms / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  return `${Math.floor(hours / 24)} day(s) ago`;
}

function severityColor(severity: string) {
  const s = severity.toLowerCase();
  if (s === 'high') return 'bg-red-400/10 text-red-400 border border-red-500/20';
  if (s === 'medium') return 'bg-amber-400/10 text-amber-400 border border-amber-500/20';
  if (s === 'low') return 'bg-blue-400/10 text-blue-400 border border-blue-500/20';
  return 'bg-slate-800 text-slate-400';
}

const ALL_SECTIONS = [
  'Dashboard',
  'Secure Chat',
  'Document Sanitizer',
  'AI Models',
  'Agents',
  'Knowledge Base',
  'Compliance',
  'Alerts',
  'Audit Log',
  'Reports',
  'Settings',
] as const;

type SectionName = (typeof ALL_SECTIONS)[number];

type SectionIconType = React.ComponentType<React.SVGProps<SVGSVGElement>>;

const SECTION_ICONS: Record<SectionName, SectionIconType> = {
  'Dashboard': Squares2X2Icon,
  'Secure Chat': ChatBubbleLeftRightIcon,
  'Document Sanitizer': DocumentMagnifyingGlassIcon,
  'AI Models': CpuChipIcon,
  'Agents': CircleStackIcon,
  'Knowledge Base': BookOpenIcon,
  'Compliance': ShieldCheckIcon,
  'Alerts': BellAlertIcon,
  'Audit Log': ClipboardDocumentListIcon,
  'Reports': ChartBarIcon,
  'Settings': Cog6ToothIcon,
};

const Dashboard: React.FC = () => {
  const router = useRouter();
  const [section, setSection] = useState<SectionName>('Dashboard');
  const [summary, setSummary] = useState<SummaryMetrics | null>(null);
  const [compliance, setCompliance] = useState<ComplianceStatus | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login');
    }
  }, [router]);

  useEffect(() => {
    let cancelled = false;

    async function fetchDashboard() {
      setLoading(true);
      setFetchError(false);
      try {
        const [metricsRes, complianceRes, alertsRes] = await Promise.all([
          apiFetch(`${API_BASE}/api/metrics/summary`),
          apiFetch(`${API_BASE}/api/compliance/status`),
          apiFetch(`${API_BASE}/api/alerts/recent`),
        ]);

        if (!metricsRes.ok || !complianceRes.ok || !alertsRes.ok) {
          throw new Error('One or more API responses were not OK');
        }

        const [metricsData, complianceData, alertsData] = await Promise.all([
          metricsRes.json(),
          complianceRes.json(),
          alertsRes.json(),
        ]);

        if (cancelled) return;

        setSummary({
          totalPrompts24h: metricsData.total_prompts_24h ?? 0,
          blockedPrompts: metricsData.blocked_prompts ?? 0,
          redactedOutputs: metricsData.redacted_outputs ?? 0,
          highRiskEvents: metricsData.high_risk_events ?? 0,
        });

        setCompliance({
          complianceScore: complianceData.compliance_score ?? 0,
          compliantControls: complianceData.compliant_controls ?? 0,
          totalControls: complianceData.total_controls ?? 0,
        });

        setAlerts(
          (alertsData.alerts ?? []).map((a: Record<string, unknown>) => ({
            id: String(a.id ?? ''),
            type: String(a.type ?? 'Security Event'),
            severity: String(a.severity ?? 'info'),
            message: String(a.message ?? ''),
            timestamp: String(a.timestamp ?? ''),
          })),
        );
      } catch {
        if (!cancelled) setFetchError(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchDashboard();
    return () => {
      cancelled = true;
    };
  }, []);

  const compliancePercent = compliance
    ? Math.round(compliance.complianceScore * 100)
    : 0;

  const renderMainContent = () => {
    if (section === 'Dashboard') {
      return (
        <>
          <header className="mb-6">
            <h1 className="text-2xl font-semibold text-slate-100">
              AI Security Dashboard
            </h1>
            <p className="text-sm text-slate-400">
              Welcome to CyberOracle — unified monitoring for all AI activity.
            </p>
          </header>

          {fetchError && (
            <div className="mb-4 rounded-lg border border-amber-500/20 bg-amber-400/5 px-4 py-3 text-xs text-amber-400">
              Backend unavailable — start the CyberOracle backend to see live
              metrics.
            </div>
          )}

          {/* TOP SUMMARY CARDS */}
          <section className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-4 mb-6">
            <SummaryCard
              title="Total Prompts (24h)"
              value={loading ? '—' : (summary?.totalPrompts24h ?? 0)}
              description="Across all apps & models"
            />
            <SummaryCard
              title="Blocked Prompts"
              value={loading ? '—' : (summary?.blockedPrompts ?? 0)}
              description="Stopped by policies & rate limits"
              valueClassName="text-red-400"
            />
            <SummaryCard
              title="Redacted Responses"
              value={loading ? '—' : (summary?.redactedOutputs ?? 0)}
              description="Outputs sanitized by DLP layer"
              valueClassName="text-amber-400"
            />
            <SummaryCard
              title="High-Risk Events"
              value={loading ? '—' : (summary?.highRiskEvents ?? 0)}
              description="risk_score above threshold"
              valueClassName="text-red-400"
            />
          </section>

          {/* MIDDLE ROW: COMPLIANCE + ALERTS */}
          <section className="grid gap-4 grid-cols-1 lg:grid-cols-3 mb-6">
            {/* Compliance card */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 lg:col-span-2">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-sm font-semibold text-slate-200">
                    Compliance Overview
                  </h2>
                  <p className="text-xs text-slate-400">
                    Current control coverage across NIST / HIPAA mappings.
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">Overall score</p>
                  <p className="text-xl font-semibold text-slate-100">
                    {loading ? '—' : `${compliancePercent}%`}
                  </p>
                </div>
              </div>

              <div className="mt-4">
                <div className="w-full h-3 rounded-full bg-slate-700 overflow-hidden">
                  <div
                    className="h-full bg-cyan-500 transition-all"
                    style={{ width: loading ? '0%' : `${compliancePercent}%` }}
                  />
                </div>
                <div className="flex justify-between mt-2 text-xs text-slate-500">
                  <span>
                    Compliant controls:{' '}
                    <span className="font-semibold text-slate-300">
                      {loading
                        ? '—'
                        : `${compliance?.compliantControls ?? 0}/${compliance?.totalControls ?? 0}`}
                    </span>
                  </span>
                  <span>
                    Non-compliant:{' '}
                    {loading
                      ? '—'
                      : (compliance?.totalControls ?? 0) -
                        (compliance?.compliantControls ?? 0)}
                  </span>
                </div>
              </div>
            </div>

            {/* Alerts card */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-5">
              <h2 className="text-sm font-semibold text-slate-200 mb-1">
                Recent Alerts
              </h2>
              <p className="text-xs text-slate-400 mb-3">
                Latest high-risk activity observed by CyberOracle.
              </p>

              {loading ? (
                <div className="flex justify-center py-4">
                  <Spinner />
                </div>
              ) : (
                <div className="space-y-3">
                  {alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="border border-slate-800 rounded-lg p-3 hover:bg-slate-800 transition"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-semibold text-slate-200">
                          {alert.type}
                        </span>
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${severityColor(alert.severity)}`}
                        >
                          {alert.severity.charAt(0).toUpperCase() +
                            alert.severity.slice(1)}{' '}
                          priority
                        </span>
                      </div>
                      <p className="text-xs text-slate-400">{alert.message}</p>
                      <p className="text-[10px] text-slate-500 mt-1">
                        {relativeTime(alert.timestamp)}
                      </p>
                    </div>
                  ))}

                  {alerts.length === 0 && (
                    <p className="text-xs text-slate-500">
                      No alerts in the last 24h.
                    </p>
                  )}
                </div>
              )}
            </div>
          </section>

          {/* GRAFANA SECTION */}
          <GrafanaPlaceholder />
        </>
      );
    }

    switch (section) {
      case 'Secure Chat':
        return <SecureChatPanel />;

      case 'Document Sanitizer':
        return <DocumentSanitizerPanel />;

      case 'AI Models':
        return (
          <ComingSoonCard
            icon={CpuChipIcon}
            title="AI Models"
            description="This view will list all connected models, routing rules, and per-model policies (RBAC, rate limits, safety settings)."
          />
        );

      case 'Agents':
        return (
          <ComingSoonCard
            icon={CircleStackIcon}
            title="Agents"
            description="This section will manage AI agents/orchestrators, their tools, and allowed trust boundaries."
          />
        );

      case 'Knowledge Base':
        return <KnowledgeBasePanel />;

      case 'Compliance':
        return <CompliancePanel />;

      case 'Alerts':
        return <AlertsPanel />;

      case 'Audit Log':
        return <AuditLogPanel />;

      case 'Reports':
        return <ReportsPanel />;

      case 'Settings':
         return <Settings />;

      default:
        return null;
    }
  };

  const [role, setRole] = useState<string>('user');

  useEffect(() => {
    const r = getRole() ?? 'user';
    setRole(r);
  }, []);

  const initials = role.slice(0, 2).toUpperCase();

  return (
    <div className="min-h-screen flex bg-slate-950">
      {/* SIDEBAR */}
      <aside className="hidden md:flex md:flex-col w-60 bg-slate-900 border-r border-slate-800">
        <div className="px-5 py-4 border-b border-slate-800">
          <div className="flex items-center gap-1.5">
            <ShieldCheckIcon className="w-4 h-4 text-cyan-400" />
            <div className="text-xs font-semibold text-cyan-400">CyberOracle</div>
          </div>
          <div className="text-sm font-semibold text-slate-200 mt-0.5">
            Secure AI Gateway
          </div>
        </div>

        <nav className="flex-1 px-2 py-4 space-y-0.5 text-sm">
          {ALL_SECTIONS.map((name) => (
            <SidebarItem
              key={name}
              label={name}
              icon={SECTION_ICONS[name]}
              active={section === name}
              onClick={() => setSection(name)}
            />
          ))}
        </nav>

        {/* Role badge + sign out */}
        <div className="px-4 py-3 border-t border-slate-800">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-cyan-400/10 border border-cyan-500/20 flex items-center justify-center">
              <span className="text-[11px] font-semibold text-cyan-400">{initials}</span>
            </div>
            <div>
              <p className="text-[10px] text-slate-500">Signed in as</p>
              <p className="text-xs font-semibold text-slate-200 capitalize">{role}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              clearAuth();
              router.push('/login');
            }}
            className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition"
          >
            <ArrowRightStartOnRectangleIcon className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="flex-1 px-4 py-6 md:px-8">{renderMainContent()}</main>
    </div>
  );
};

export default Dashboard;

// --- Presentational components ---

function SummaryCard(props: {
  title: string;
  value: number | string;
  description: string;
  valueClassName?: string;
}) {
  const { title, value, description, valueClassName } = props;
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <p className="text-xs font-medium text-slate-400 mb-1">{title}</p>
      <p className={`text-2xl font-semibold ${valueClassName ?? 'text-slate-100'}`}>
        {value}
      </p>
      <p className="text-xs text-slate-500 mt-1">{description}</p>
    </div>
  );
}

function SidebarItem({
  label,
  icon: Icon,
  active = false,
  onClick,
}: {
  label: string;
  icon: SectionIconType;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        'w-full text-left flex items-center gap-2.5 px-3 py-2 text-xs font-medium cursor-pointer transition rounded-lg ' +
        (active
          ? 'border-l-2 border-cyan-400 bg-cyan-400/10 text-cyan-400 rounded-l-none pl-2.5'
          : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200')
      }
    >
      <Icon className="w-4 h-4 shrink-0" />
      <span>{label}</span>
    </button>
  );
}

function ComingSoonCard({
  icon: Icon,
  title,
  description,
}: {
  icon: SectionIconType;
  title: string;
  description: string;
}) {
  return (
    <div className="mt-4">
      <h1 className="text-2xl font-semibold text-slate-100 mb-2">{title}</h1>
      <p className="text-sm text-slate-400 mb-6">{description}</p>
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 flex flex-col items-center text-center">
        <div className="w-16 h-16 rounded-full bg-cyan-400/10 flex items-center justify-center mb-4">
          <Icon className="w-8 h-8 text-cyan-400" />
        </div>
        <h2 className="text-base font-semibold text-slate-100 mb-2">{title}</h2>
        <p className="text-sm text-slate-400 max-w-sm mb-4">{description}</p>
        <span className="inline-block rounded-full bg-cyan-400/10 border border-cyan-500/30 px-3 py-1 text-xs font-semibold text-cyan-400">
          Coming in Capstone II
        </span>
      </div>
    </div>
  );
}

function GrafanaPlaceholder() {
  const grafanaUrl = process.env.NEXT_PUBLIC_GRAFANA_URL;
  return (
    <section className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-200">
            Metrics &amp; Observability
          </h2>
          <p className="text-xs text-slate-400">
            Grafana dashboard integration
          </p>
        </div>
        {grafanaUrl && (
          <a
            href={grafanaUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 rounded-lg bg-slate-800 border border-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 transition"
          >
            <ArrowTopRightOnSquareIcon className="w-3.5 h-3.5" />
            Open Grafana
          </a>
        )}
      </div>
      <div className="border border-dashed border-slate-700 rounded-xl px-6 py-12 text-center">
        <p className="text-sm text-slate-400 mb-1">
          Configure{' '}
          <code className="font-mono text-xs bg-slate-800 rounded px-1 text-slate-300">
            GRAFANA_URL
          </code>{' '}
          in{' '}
          <code className="font-mono text-xs bg-slate-800 rounded px-1 text-slate-300">
            .env
          </code>{' '}
          to embed live dashboards here.
        </p>
        <p className="text-xs text-slate-500">
          Prometheus + Loki + Grafana stack available in docker-compose.yml
        </p>
      </div>
    </section>
  );
}


