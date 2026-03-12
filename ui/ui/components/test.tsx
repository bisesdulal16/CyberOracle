'use client';

import React, { useState } from 'react';
import SecureChatPanel from './SecureChatPanel';

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
  severity: 'Low' | 'Medium' | 'High';
  message: string;
  timestamp: string;
};

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
      return (
        <>
          <header className="mb-6">
            <h1 className="text-2xl font-semibold text-slate-900">
              AI Security Dashboard
            </h1>
            <p className="text-sm text-slate-500">
              Welcome to CyberOracle — unified monitoring for all AI activity.
            </p>
          </header>

          <section className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-4 mb-6">
            <SummaryCard title="Total Prompts (24h)" value={summary.totalPrompts24h} description="Across all apps & models" />
            <SummaryCard title="Blocked Prompts" value={summary.blockedPrompts} description="Stopped by policies & rate limits" valueClassName="text-rose-600" />
            <SummaryCard title="Redacted Responses" value={summary.redactedOutputs} description="Outputs sanitized by DLP layer" valueClassName="text-amber-600" />
            <SummaryCard title="High-Risk Events" value={summary.highRiskEvents} description="risk_score above threshold" valueClassName="text-red-600" />
          </section>

          <section className="grid gap-4 grid-cols-1 lg:grid-cols-3 mb-6">
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm lg:col-span-2">
              <h2 className="text-sm font-semibold text-slate-900 mb-3">Compliance Overview</h2>
              <div className="w-full h-3 rounded-full bg-slate-100 overflow-hidden">
                <div className="h-full bg-blue-500 transition-all" style={{ width: `${compliancePercent}%` }} />
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <h2 className="text-sm font-semibold text-slate-900 mb-3">Recent Alerts</h2>
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div key={alert.id} className="border p-3 rounded-lg">
                    <div className="flex justify-between mb-1">
                      <span className="text-xs font-semibold">{alert.type}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${severityColor(alert.severity)}`}>
                        {alert.severity}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600">{alert.message}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <iframe src={GRAFANA_IFRAME_URL} className="w-full h-[380px] rounded-lg border border-slate-200" />
          </section>
        </>
      );
    }

    switch (section) {
      case 'Secure Chat':
        return <SecureChatPanel />;
      case 'Settings':
        return <SettingsView />;
      default:
        return (
          <div className="mt-4">
            <h1 className="text-2xl font-semibold text-slate-900 mb-2">{section}</h1>
            <div className="mt-4 rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-xs text-slate-500">
              This section is under development.
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen flex bg-slate-50">
      <aside className="hidden md:flex md:flex-col w-60 bg-white border-r border-slate-200">
        <div className="px-5 py-4 border-b border-slate-100">
          <div className="text-xs font-semibold text-sky-500">CyberOracle</div>
          <div className="text-sm font-semibold text-slate-900">Secure AI Gateway</div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 text-sm">
          {ALL_SECTIONS.map((name) => (
            <SidebarItem key={name} label={name} active={section === name} onClick={() => setSection(name)} />
          ))}
        </nav>
      </aside>

      <main className="flex-1 px-4 py-6 md:px-8">{renderMainContent()}</main>
    </div>
  );
};

export default Dashboard;

/* ================= SETTINGS VIEW ================= */

function SettingsView() {
  const [activeTab, setActiveTab] = useState('Profile');
  const [twoFactor, setTwoFactor] = useState(true);
  const [emailNotif, setEmailNotif] = useState(true);

  const tabs = ['Profile', 'Notifications', 'Security', 'Appearance', 'Integrations', 'System'];

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900 mb-1">Settings</h1>
      <p className="text-sm text-slate-500 mb-6">Manage your account and platform settings</p>

      <div className="flex gap-6">
        <div className="w-64 bg-white border border-slate-200 rounded-xl p-3 shadow-sm">
          {tabs.map((tab) => (
            <button key={tab} onClick={() => setActiveTab(tab)} className={`w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition ${
              activeTab === tab ? 'bg-sky-50 text-sky-700 border border-sky-100' : 'text-slate-600 hover:bg-slate-50'
            }`}>
              {tab}
            </button>
          ))}
        </div>

        <div className="flex-1 bg-white border border-slate-200 rounded-xl p-8 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900 mb-6">Profile Settings</h2>

          <h3 className="text-sm font-semibold text-slate-900 mb-4">Personal Information</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <LabeledInput label="Full Name" defaultValue="Olivia Carter" />
            <LabeledInput label="Email Address" defaultValue="olivia.carter@cyberoracle.com" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            <LabeledSelect label="Role" options={['Select a role', 'Admin', 'Manager', 'Analyst', 'Developer']} />
            <LabeledSelect label="Department" options={['Select a department', 'Engineering', 'Security', 'Operations', 'Compliance']} />
          </div>

          <h3 className="text-sm font-semibold text-slate-900 mb-4">Preferences</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            <LabeledSelect label="Language" options={['Select a language', 'English', 'Spanish', 'French']} />
            <LabeledSelect label="Timezone" options={['Select a timezone', 'UTC', 'EST', 'CST', 'PST']} />
          </div>

          <div className="space-y-6 mb-8">
            <Toggle title="Two-Factor Authentication" description="Enable two-factor authentication for your account" enabled={twoFactor} onToggle={() => setTwoFactor(!twoFactor)} />
            <Toggle title="Email Notifications" description="Receive email notifications for important updates" enabled={emailNotif} onToggle={() => setEmailNotif(!emailNotif)} />
          </div>

          <button className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition">
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}

function LabeledInput({ label, defaultValue }: { label: string; defaultValue: string }) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-800 mb-1">{label}</label>
      <input defaultValue={defaultValue} className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm text-black focus:outline-none focus:ring-2 focus:ring-blue-500" />
    </div>
  );
}

function LabeledSelect({ label, options }: { label: string; options: string[] }) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-800 mb-1">{label}</label>
      <select className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm text-black bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
        {options.map((opt) => (
          <option key={opt}>{opt}</option>
        ))}
      </select>
    </div>
  );
}

function Toggle({ title, description, enabled, onToggle }: any) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-slate-900">{title}</p>
        <p className="text-xs text-slate-500">{description}</p>
      </div>
      <button onClick={onToggle} className={`w-11 h-6 rounded-full transition ${enabled ? 'bg-purple-600' : 'bg-slate-300'}`}>
        <div className={`h-5 w-5 bg-white rounded-full shadow transform transition ${enabled ? 'translate-x-5' : 'translate-x-1'}`} />
      </button>
    </div>
  );
}

function SummaryCard({ title, value, description, valueClassName }: any) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
      <p className="text-xs font-medium text-slate-500 mb-1">{title}</p>
      <p className={`text-2xl font-semibold ${valueClassName ?? 'text-slate-900'}`}>{value}</p>
      <p className="text-xs text-slate-400 mt-1">{description}</p>
    </div>
  );
}

function SidebarItem({ label, active, onClick }: any) {
  return (
    <button onClick={onClick} className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition ${
      active ? 'bg-sky-50 text-sky-700 border border-sky-100' : 'text-slate-600 hover:bg-slate-50'
    }`}>
      {label}
    </button>
  );
}
