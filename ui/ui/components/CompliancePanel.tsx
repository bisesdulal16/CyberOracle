'use client';

import React, { useState, useEffect } from 'react';
import { apiFetch } from '../lib/auth';
import { ArrowDownTrayIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8001';

type ControlStatus = 'compliant' | 'partial' | 'non-compliant';

type Control = {
  name: string;
  status: ControlStatus;
};

type FrameworkData = {
  score: number;
  compliant: number;
  total: number;
  status: string;
};

type ComplianceAPIResponse = {
  compliance_score: number;
  compliant_controls: number;
  total_controls: number;
  frameworks: Record<string, FrameworkData>;
};

const FRAMEWORK_CONTROLS: Record<string, Control[]> = {
  HIPAA: [
    { name: 'Authentication & Session Management (JWT + API Keys)', status: 'compliant' },
    { name: 'PHI Detection via DLP (Presidio + Regex)', status: 'compliant' },
    { name: 'Audit Logging (structured LogEntry, encrypted)', status: 'compliant' },
    { name: 'Encryption at Rest (Fernet / AES-256)', status: 'compliant' },
    { name: 'Transmission Security (TLS configuration)', status: 'compliant' },
    { name: 'Minimum Necessary Access (DLP redacts, not full-block)', status: 'compliant' },
    { name: 'Incident Response Alerting (Discord / alert_manager)', status: 'compliant' },
    { name: 'Rate Limiting Controls', status: 'compliant' },
    { name: 'Risk Assessment Documentation (threat model)', status: 'compliant' },
    { name: 'De-identification Capability (Presidio anonymizer)', status: 'compliant' },
    { name: 'Data Retention Policy (90-day configuration)', status: 'compliant' },
    { name: 'Backup & Recovery (DB backup scripts)', status: 'compliant' },
    { name: 'Breach Notification (alert triggers configured)', status: 'compliant' },
    { name: 'Security Event Monitoring (Prometheus / Loki / Grafana)', status: 'compliant' },
    { name: 'Vulnerability Scanning (TruffleHog in CI)', status: 'compliant' },
    { name: 'Red Team / Penetration Testing (synthetic dataset)', status: 'compliant' },
    { name: 'RBAC Policy Enforcement (policy.yaml written, not enforced in FastAPI)', status: 'partial' },
    { name: 'Workforce Access Controls (role assignment not automated)', status: 'partial' },
    { name: 'Physical Safeguards (out of scope — Capstone I)', status: 'non-compliant' },
    { name: 'Business Associate Agreement Management', status: 'non-compliant' },
  ],
  FERPA: [
    { name: 'Student Record Access Controls (RBAC roles defined)', status: 'compliant' },
    { name: 'Audit Trail for Record Access (LogEntry)', status: 'compliant' },
    { name: 'DLP for Student PII (SSN, email detection)', status: 'compliant' },
    { name: 'Encryption of Student Data at Rest', status: 'compliant' },
    { name: 'Authentication Requirements (JWT)', status: 'compliant' },
    { name: 'Data Sharing Controls (DLP blocks exfiltration)', status: 'compliant' },
    { name: 'Logging of Disclosures (structured audit log)', status: 'compliant' },
    { name: 'Role-based Access (Admin / Developer / Auditor)', status: 'compliant' },
    { name: 'Directory Information Policy (RBAC not enforced in FastAPI)', status: 'partial' },
    { name: 'Annual Compliance Review Procedures', status: 'non-compliant' },
  ],
  NIST_CSF: [
    { name: 'Identify — Asset Management', status: 'compliant' },
    { name: 'Identify — Risk Assessment (threat model docs)', status: 'compliant' },
    { name: 'Protect — Access Control (JWT / RBAC policy)', status: 'compliant' },
    { name: 'Protect — Data Security (Fernet encryption + DLP)', status: 'compliant' },
    { name: 'Protect — Protective Technology (middleware stack)', status: 'compliant' },
    { name: 'Detect — Anomalies & Events (alert_manager)', status: 'compliant' },
    { name: 'Detect — Continuous Monitoring (Prometheus / Loki)', status: 'compliant' },
    { name: 'Detect — Detection Processes (red-team test suite)', status: 'compliant' },
    { name: 'Respond — Response Planning (Discord alerts + n8n partial)', status: 'compliant' },
    { name: 'Recover — Recovery Planning (backup scripts, partial)', status: 'partial' },
    { name: 'Govern — Supply Chain Risk Management', status: 'non-compliant' },
  ],
  GDPR: [
    { name: 'Lawful Basis for Data Processing', status: 'compliant' },
    { name: 'Data Minimization (DLP redacts, does not log raw PII)', status: 'compliant' },
    { name: 'Right to Erasure (data retention policy configured)', status: 'compliant' },
    { name: 'Data Security (encryption + DLP middleware)', status: 'compliant' },
    { name: 'Breach Notification (alerting system configured)', status: 'compliant' },
    { name: 'Privacy by Design (DLP enforced at gateway layer)', status: 'compliant' },
    { name: 'Data Protection Documentation (policy.yaml + audit logs)', status: 'compliant' },
    { name: 'Cross-border Transfer Controls (local Ollama, no cloud LLM)', status: 'compliant' },
    { name: 'Consent Management (not implemented in Capstone I)', status: 'partial' },
  ],
};

const DLP_RULES = [
  { pattern: 'SSN', description: 'U.S. Social Security Numbers', severity: 'Critical', mode: 'Block + Redact' },
  { pattern: 'Credit Card', description: 'Credit/debit card numbers (13–16 digits)', severity: 'Critical', mode: 'Block + Redact' },
  { pattern: 'API Key', description: 'Exposed API keys or tokens in request payloads', severity: 'High', mode: 'Block + Redact' },
  { pattern: 'Email Address', description: 'Email addresses in prompts and responses', severity: 'Medium', mode: 'Redact' },
];

const FRAMEWORK_TABS = ['HIPAA', 'FERPA', 'NIST_CSF', 'GDPR'] as const;
type Framework = (typeof FRAMEWORK_TABS)[number];

const FRAMEWORK_LABELS: Record<Framework, string> = {
  HIPAA: 'HIPAA',
  FERPA: 'FERPA',
  NIST_CSF: 'NIST CSF',
  GDPR: 'GDPR',
};

function statusBadge(status: ControlStatus) {
  switch (status) {
    case 'compliant':
      return 'bg-emerald-400/10 text-emerald-400 border border-emerald-500/20';
    case 'partial':
      return 'bg-amber-400/10 text-amber-400 border border-amber-500/20';
    case 'non-compliant':
      return 'bg-red-400/10 text-red-400 border border-red-500/20';
  }
}

function statusLabel(status: ControlStatus) {
  switch (status) {
    case 'compliant': return 'Compliant';
    case 'partial': return 'Partial';
    case 'non-compliant': return 'Non-compliant';
  }
}

function dlpSeverityColor(severity: string) {
  switch (severity) {
    case 'Critical': return 'bg-red-400/10 text-red-400 border border-red-500/20';
    case 'High': return 'bg-amber-400/10 text-amber-400 border border-amber-500/20';
    default: return 'bg-blue-400/10 text-blue-400 border border-blue-500/20';
  }
}

function handleExport(framework: Framework, frameworkData: FrameworkData | undefined) {
  const controls = FRAMEWORK_CONTROLS[framework] ?? [];
  const label = FRAMEWORK_LABELS[framework];
  const score = frameworkData ? Math.round(frameworkData.score * 100) : 0;

  const rows: string[][] = [
    ['CyberOracle Compliance Export'],
    ['Framework', label],
    ['Score', `${score}%`],
    ['Compliant Controls', String(frameworkData?.compliant ?? 0)],
    ['Total Controls', String(frameworkData?.total ?? 0)],
    ['Generated', new Date().toISOString()],
    [],
    ['Control', 'Status'],
    ...controls.map((c) => [c.name, statusLabel(c.status)]),
    [],
    ['DLP Rules'],
    ['Pattern', 'Description', 'Severity', 'Mode'],
    ...DLP_RULES.map((r) => [r.pattern, r.description, r.severity, r.mode]),
  ];

  const csv = rows.map((r) => r.map((cell) => `"${cell}"`).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `cyberoracle-${label.replace(' ', '-').toLowerCase()}-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function CompliancePanel() {
  const [activeTab, setActiveTab] = useState<Framework>('HIPAA');
  const [apiData, setApiData] = useState<ComplianceAPIResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function fetchCompliance() {
      setLoading(true);
      setFetchError(false);
      try {
        const res = await apiFetch(`${API_BASE}/api/compliance/status`);
        if (!res.ok) throw new Error('API error');
        const data: ComplianceAPIResponse = await res.json();
        if (!cancelled) setApiData(data);
      } catch {
        if (!cancelled) setFetchError(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchCompliance();
    return () => { cancelled = true; };
  }, []);

  const overallScore = apiData ? Math.round(apiData.compliance_score * 100) : 0;
  const activeFramework = apiData?.frameworks[activeTab];
  const controls = FRAMEWORK_CONTROLS[activeTab] ?? [];
  const frameworkScore = activeFramework ? Math.round(activeFramework.score * 100) : 0;

  return (
    <div className="mt-4 max-w-4xl">
      <div className="flex items-start justify-between mb-1">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">Compliance</h1>
          <p className="text-sm text-slate-400">
            Control coverage across HIPAA, FERPA, NIST CSF, and GDPR.
          </p>
        </div>
        <button
          type="button"
          onClick={() => handleExport(activeTab, activeFramework)}
          className="mt-1 flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold rounded-lg border border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700 transition"
        >
          <ArrowDownTrayIcon className="w-3.5 h-3.5" />
          Export CSV
        </button>
      </div>

      {fetchError && (
        <div className="mt-3 mb-4 rounded-lg border border-amber-500/20 bg-amber-400/5 px-4 py-3 text-xs text-amber-400">
          Backend unavailable — showing last known compliance status.
        </div>
      )}

      {/* Overall summary row */}
      <div className="grid grid-cols-3 gap-4 mt-5 mb-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
          <p className="text-xs text-slate-400 mb-1">Overall score</p>
          <p className="text-2xl font-semibold text-slate-100">
            {loading ? (
              <ArrowPathIcon className="animate-spin w-5 h-5 text-cyan-400 mx-auto" />
            ) : `${overallScore}%`}
          </p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
          <p className="text-xs text-slate-400 mb-1">Compliant controls</p>
          <p className="text-2xl font-semibold text-emerald-400">
            {loading ? '—' : (apiData?.compliant_controls ?? 0)}
          </p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
          <p className="text-xs text-slate-400 mb-1">Non-compliant</p>
          <p className="text-2xl font-semibold text-red-400">
            {loading ? '—' : (apiData?.total_controls ?? 0) - (apiData?.compliant_controls ?? 0)}
          </p>
        </div>
      </div>

      {/* Framework tabs */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl mb-6 overflow-hidden">
        {/* Tab bar */}
        <div className="flex border-b border-slate-800">
          {FRAMEWORK_TABS.map((fw) => (
            <button
              key={fw}
              type="button"
              onClick={() => setActiveTab(fw)}
              className={
                'flex-1 py-3 text-xs font-semibold transition ' +
                (activeTab === fw
                  ? 'border-b-2 border-cyan-400 text-cyan-400 bg-cyan-400/5'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800')
              }
            >
              {FRAMEWORK_LABELS[fw]}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="p-5">
          {/* Framework score bar */}
          <div className="mb-5">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-semibold text-slate-300">
                {FRAMEWORK_LABELS[activeTab]} Coverage
              </span>
              <span className="text-xs text-slate-500">
                {loading ? '—' : `${activeFramework?.compliant ?? 0} / ${activeFramework?.total ?? 0} controls`}
                <span className="ml-2 font-semibold text-slate-300">
                  {loading ? '' : `${frameworkScore}%`}
                </span>
              </span>
            </div>
            <div className="w-full h-2.5 rounded-full bg-slate-700 overflow-hidden">
              <div
                className="h-full bg-cyan-500 transition-all duration-500"
                style={{ width: loading ? '0%' : `${frameworkScore}%` }}
              />
            </div>
          </div>

          {/* Controls list */}
          <div className="space-y-1">
            {controls.map((control) => (
              <div
                key={control.name}
                className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0 hover:bg-slate-800 px-2 rounded-lg transition"
              >
                <span className="text-xs text-slate-300 pr-4">
                  {control.name}
                </span>
                <span
                  className={`shrink-0 text-[10px] px-2 py-0.5 rounded-full font-semibold ${statusBadge(control.status)}`}
                >
                  {statusLabel(control.status)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* DLP Rules table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-semibold text-slate-200">
              Active DLP Rules
            </h2>
            <p className="text-xs text-slate-400">
              Sourced from{' '}
              <code className="font-mono text-xs bg-slate-800 rounded px-1 text-slate-300">
                policy.yaml
              </code>{' '}
              — applied to all AI requests and document uploads.
            </p>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-400/10 text-emerald-400 border border-emerald-500/20 font-semibold">
            All Active
          </span>
        </div>

        <table className="w-full text-xs">
          <thead>
            <tr className="text-left text-slate-400 bg-slate-800 border-b border-slate-700">
              <th className="pb-2 pt-2 px-3 font-medium">Pattern</th>
              <th className="pb-2 pt-2 px-3 font-medium">Description</th>
              <th className="pb-2 pt-2 px-3 font-medium">Severity</th>
              <th className="pb-2 pt-2 px-3 font-medium">Enforcement</th>
            </tr>
          </thead>
          <tbody>
            {DLP_RULES.map((rule) => (
              <tr
                key={rule.pattern}
                className="border-b border-slate-800 last:border-0 hover:bg-slate-800 transition"
              >
                <td className="py-2.5 px-3 font-semibold text-slate-200">
                  {rule.pattern}
                </td>
                <td className="py-2.5 px-3 text-slate-400">{rule.description}</td>
                <td className="py-2.5 px-3">
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${dlpSeverityColor(rule.severity)}`}>
                    {rule.severity}
                  </span>
                </td>
                <td className="py-2.5 px-3 text-slate-400">{rule.mode}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
