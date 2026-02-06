'use client';

import React, { useState } from 'react';

type SummaryMetrics = {
  totalPrompts24h: number;
  blockedPrompts: number;
  redactedOutputs: number;
  highRiskEvents: number;
};

type ComplianceStatus = {
  complianceScore: number; // 0–1
  compliantControls: number;
  totalControls: number;
};

type AlertItem = {
  id: string;
  type: string;
  severity: 'Low' | 'Medium' | 'High';
  message: string;
  timestamp: string;
};

// ------- MOCK DATA FOR NOW (no backend needed) -------

const MOCK_SUMMARY: SummaryMetrics = {
  totalPrompts24h: 486,
  blockedPrompts: 23,
  redactedOutputs: 51,
  highRiskEvents: 7,
};

const MOCK_COMPLIANCE: ComplianceStatus = {
  complianceScore: 0.82,
  compliantControls: 41,
  totalControls: 50,
};

const MOCK_ALERTS: AlertItem[] = [
  {
    id: '1',
    type: 'Prompt Injection',
    severity: 'High',
    message: 'System prompt extraction attempt detected',
    timestamp: '10 min ago',
  },
  {
    id: '2',
    type: 'Model Misuse',
    severity: 'Medium',
    message: 'Unauthorized model requested by support-bot role',
    timestamp: '1 hour ago',
  },
  {
    id: '3',
    type: 'Data Exfiltration',
    severity: 'High',
    message: 'Possible PHI leak blocked by DLP',
    timestamp: '3 hours ago',
  },
];

// Replace this when Grafana is ready
const GRAFANA_IFRAME_URL = 'about:blank';

function severityColor(severity: AlertItem['severity']) {
  switch (severity) {
    case 'High':
      return 'bg-red-100 text-red-700';
    case 'Medium':
      return 'bg-yellow-100 text-yellow-800';
    default:
      return 'bg-blue-100 text-blue-700';
  }
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

const Dashboard: React.FC = () => {
  const [section, setSection] = useState<SectionName>('Dashboard');

  const summary = MOCK_SUMMARY;
  const compliance = MOCK_COMPLIANCE;
  const alerts = MOCK_ALERTS;

  const compliancePercent = Math.round(compliance.complianceScore * 100);

  const renderMainContent = () => {
    if (section === 'Dashboard') {
      // --- MAIN DASHBOARD VIEW ---
      return (
        <>
          {/* HEADER */}
          <header className="mb-6">
            <h1 className="text-2xl font-semibold text-slate-900">
              AI Security Dashboard
            </h1>
            <p className="text-sm text-slate-500">
              Welcome to CyberOracle — unified monitoring for all AI activity.
            </p>
          </header>

          {/* TOP SUMMARY CARDS */}
          <section className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-4 mb-6">
            <SummaryCard
              title="Total Prompts (24h)"
              value={summary.totalPrompts24h}
              description="Across all apps & models"
            />
            <SummaryCard
              title="Blocked Prompts"
              value={summary.blockedPrompts}
              description="Stopped by policies & rate limits"
              valueClassName="text-rose-600"
            />
            <SummaryCard
              title="Redacted Responses"
              value={summary.redactedOutputs}
              description="Outputs sanitized by DLP layer"
              valueClassName="text-amber-600"
            />
            <SummaryCard
              title="High-Risk Events"
              value={summary.highRiskEvents}
              description="risk_score above threshold"
              valueClassName="text-red-600"
            />
          </section>

          {/* MIDDLE ROW: COMPLIANCE + ALERTS */}
          <section className="grid gap-4 grid-cols-1 lg:grid-cols-3 mb-6">
            {/* Compliance card */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm lg:col-span-2">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-sm font-semibold text-slate-900">
                    Compliance Overview
                  </h2>
                  <p className="text-xs text-slate-500">
                    Current control coverage across NIST / HIPAA mappings.
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">Overall score</p>
                  <p className="text-xl font-semibold text-slate-900">
                    {compliancePercent}%
                  </p>
                </div>
              </div>

              <div className="mt-4">
                <div className="w-full h-3 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all"
                    style={{ width: `${compliancePercent}%` }}
                  />
                </div>
                <div className="flex justify-between mt-2 text-xs text-slate-500">
                  <span>
                    Compliant controls:{' '}
                    <span className="font-semibold text-slate-800">
                      {compliance.compliantControls}/{compliance.totalControls}
                    </span>
                  </span>
                  <span>
                    Non-compliant:{' '}
                    {compliance.totalControls - compliance.compliantControls}
                  </span>
                </div>
              </div>
            </div>

            {/* Alerts card */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <h2 className="text-sm font-semibold text-slate-900 mb-1">
                Recent Alerts
              </h2>
              <p className="text-xs text-slate-500 mb-3">
                Latest high-risk activity observed by CyberOracle.
              </p>

              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="border border-slate-100 rounded-lg p-3 hover:bg-slate-50 cursor-pointer transition"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-slate-800">
                        {alert.type}
                      </span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${severityColor(
                          alert.severity,
                        )}`}
                      >
                        {alert.severity} priority
                      </span>
                    </div>
                    <p className="text-xs text-slate-600">{alert.message}</p>
                    <p className="text-[10px] text-slate-400 mt-1">
                      {alert.timestamp}
                    </p>
                  </div>
                ))}

                {alerts.length === 0 && (
                  <p className="text-xs text-slate-400">No alerts in the last 24h.</p>
                )}
              </div>
            </div>
          </section>

          {/* GRAFANA SECTION */}
          <section className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">
                  Violations & Risk Over Time
                </h2>
                <p className="text-xs text-slate-500">
                  Embedded Grafana dashboard for deeper observability.
                </p>
              </div>
            </div>

            <div className="mt-2">
              <iframe
                src={GRAFANA_IFRAME_URL}
                className="w-full h-[380px] rounded-lg border border-slate-200"
                title="CyberOracle Grafana Dashboard"
              />
            </div>
          </section>
        </>
      );
    }

    // --- PLACEHOLDERS FOR OTHER SECTIONS ---
    switch (section) {
      case 'Secure Chat':
        return (
          <SectionPlaceholder
            title="Secure Chat"
            description="This section will host the secure chat interface that talks to CyberOracle's /ai/query gateway. It will show prompt history, risk scores, and redaction indicators inline."
          />
        );
      case 'Document Sanitizer':
        return (
          <SectionPlaceholder
            title="Document Sanitizer"
            description="Here you will upload files and see DLP redactions, PII detection, and safe exports before they are sent to any LLM."
          />
        );
      case 'AI Models':
        return (
          <SectionPlaceholder
            title="AI Models"
            description="This view will list all connected models, routing rules, and per-model policies (RBAC, rate limits, safety settings)."
          />
        );
      case 'Agents':
        return (
          <SectionPlaceholder
            title="Agents"
            description="This section will manage AI agents/orchestrators, their tools, and allowed trust boundaries."
          />
        );
      case 'Knowledge Base':
        return (
          <SectionPlaceholder
            title="Knowledge Base"
            description="This is where RAG collections, sensitivity labels, and ingestion policies will live."
          />
        );
      case 'Compliance':
        return (
          <SectionPlaceholder
            title="Compliance"
            description="Here you will see NIST / HIPAA / FERPA mappings, control coverage, and exportable reports for auditors."
          />
        );
      case 'Alerts':
        return (
          <SectionPlaceholder
            title="Alerts"
            description="This view will show a full alert feed with filters for severity, model, app, and attack type."
          />
        );
      case 'Audit Log':
        return (
          <SectionPlaceholder
            title="Audit Log"
            description="This section will expose a searchable audit trail of all prompts, tool calls, and DLP decisions."
          />
        );
      case 'Reports':
        return (
          <SectionPlaceholder
            title="Reports"
            description="Here we will surface scheduled reports, PDF exports, and Grafana-linked views for leadership."
          />
        );
      case 'Settings':
        return (
          <SectionPlaceholder
            title="Settings"
            description="This area will manage tenants, API keys, RBAC roles, and integration settings."
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* SIDEBAR */}
      <aside className="hidden md:flex md:flex-col w-60 bg-white border-r border-slate-200">
        <div className="px-5 py-4 border-b border-slate-100">
          <div className="text-xs font-semibold text-sky-500">CyberOracle</div>
          <div className="text-sm font-semibold text-slate-900">
            Secure AI Gateway
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 text-sm">
          {ALL_SECTIONS.map((name) => (
            <SidebarItem
              key={name}
              label={name}
              active={section === name}
              onClick={() => setSection(name)}
            />
          ))}
        </nav>
      </aside>

      {/* MAIN CONTENT */}
      <main className="flex-1 px-4 py-6 md:px-8">{renderMainContent()}</main>
    </div>
  );
};

export default Dashboard;

// --- Small presentational components ---

function SummaryCard(props: {
  title: string;
  value: number | string;
  description: string;
  valueClassName?: string;
}) {
  const { title, value, description, valueClassName } = props;
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
      <p className="text-xs font-medium text-slate-500 mb-1">{title}</p>
      <p className={`text-2xl font-semibold ${valueClassName ?? 'text-slate-900'}`}>
        {value}
      </p>
      <p className="text-xs text-slate-400 mt-1">{description}</p>
    </div>
  );
}

function SidebarItem({
  label,
  active = false,
  onClick,
}: {
  label: string;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        'w-full text-left flex items-center rounded-lg px-3 py-2 text-xs font-medium cursor-pointer transition ' +
        (active
          ? 'bg-sky-50 text-sky-700 border border-sky-100'
          : 'text-slate-600 hover:bg-slate-50')
      }
    >
      <span>{label}</span>
    </button>
  );
}

function SectionPlaceholder(props: { title: string; description: string }) {
  const { title, description } = props;
  return (
    <div className="mt-4">
      <h1 className="text-2xl font-semibold text-slate-900 mb-2">{title}</h1>
      <p className="text-sm text-slate-500 max-w-2xl">{description}</p>
      <div className="mt-4 rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-xs text-slate-500">
        This is a placeholder view. As CyberOracle evolves, this section will be
        wired to the corresponding backend APIs, DLP reports, and security
        controls.
      </div>
    </div>
  );
}
