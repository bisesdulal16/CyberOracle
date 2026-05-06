'use client';

import React, { useEffect, useState } from 'react';
import { apiFetch } from '../lib/auth';
import { getRole, getToken } from '../lib/auth';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8001';

// ─── types ───────────────────────────────────────────────────────────────────

type Role = 'admin' | 'developer' | 'auditor';

type MeResponse = { username: string; role: Role };

type ModelOption = { id: string; label: string; provider: string };

type DlpRule = { name: string; severity: 'critical' | 'high' | 'medium' | 'low'; description: string };

type OverviewResponse = {
  dlp: { enabled: boolean; block_on_detection: boolean; redact_mode: string; rules: DlpRule[] };
  rate_limits: { enabled: boolean; window_seconds: number; per_role: Record<string, number> };
  compliance: { frameworks: string[]; log_retention_days: number; encryption_standard: string; audit_trail_required: boolean };
  integrations: { discord: boolean; slack: boolean };
  encryption: { enabled: boolean; key_id: string | null };
};

// ─── helpers ─────────────────────────────────────────────────────────────────

const SEVERITY_COLOURS: Record<string, string> = {
  critical: 'text-red-400 bg-red-400/10 border-red-500/20',
  high: 'text-orange-400 bg-orange-400/10 border-orange-500/20',
  medium: 'text-yellow-400 bg-yellow-400/10 border-yellow-500/20',
  low: 'text-green-400 bg-green-400/10 border-green-500/20',
};

const PROVIDER_COLOURS: Record<string, string> = {
  ollama: 'text-cyan-400 bg-cyan-400/10 border-cyan-500/20',
  openai: 'text-green-400 bg-green-400/10 border-green-500/20',
  anthropic: 'text-purple-400 bg-purple-400/10 border-purple-500/20',
  gemini: 'text-yellow-400 bg-yellow-400/10 border-yellow-500/20',
  groq: 'text-orange-400 bg-orange-400/10 border-orange-500/20',
};

const ROLE_COLOURS: Record<string, string> = {
  admin: 'text-red-400 bg-red-400/10 border-red-500/20',
  developer: 'text-cyan-400 bg-cyan-400/10 border-cyan-500/20',
  auditor: 'text-purple-400 bg-purple-400/10 border-purple-500/20',
};

function Badge({ label, colour }: { label: string; colour: string }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${colour}`}>
      {label}
    </span>
  );
}

function StatusDot({ on, label }: { on: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className={`w-2 h-2 rounded-full ${on ? 'bg-green-400' : 'bg-slate-600'}`} />
      <span className={`text-sm ${on ? 'text-slate-200' : 'text-slate-500'}`}>{label}</span>
    </div>
  );
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 mb-4">
      <h3 className="text-sm font-semibold text-slate-300 mb-4 pb-2 border-b border-slate-800">{title}</h3>
      {children}
    </div>
  );
}

function LockCard({ tab }: { tab: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-12 h-12 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center mb-4">
        <svg className="w-6 h-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      </div>
      <p className="text-slate-400 text-sm font-medium">{tab} requires admin access</p>
      <p className="text-slate-600 text-xs mt-1">Contact your administrator to view this section.</p>
    </div>
  );
}

function getTokenExpiry(): Date | null {
  const token = getToken();
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp ? new Date(payload.exp * 1000) : null;
  } catch {
    return null;
  }
}

// ─── tab components ───────────────────────────────────────────────────────────

function ProfileTab({ role }: { role: Role }) {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const expiry = getTokenExpiry();

  useEffect(() => {
    apiFetch(`${API_BASE}/auth/me`)
      .then((r) => r.ok ? r.json() : null)
      .then((d) => d && setMe(d))
      .catch(() => {});
  }, []);

  async function generateKey() {
    setGenerating(true);
    setError(null);
    try {
      const r = await apiFetch(`${API_BASE}/auth/apikey/generate`, { method: 'POST' });
      if (r.status === 403) { setError('Only admins can generate API keys.'); return; }
      if (!r.ok) { setError('Failed to generate key.'); return; }
      const d = await r.json();
      setApiKey(d.api_key);
    } catch {
      setError('Request failed.');
    } finally {
      setGenerating(false);
    }
  }

  function copyKey() {
    if (!apiKey) return;
    navigator.clipboard.writeText(apiKey).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div>
      <SectionCard title="Account">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-slate-500 mb-1">Username</p>
            <p className="text-sm text-slate-100 font-medium">{me?.username ?? '—'}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Role</p>
            {me?.role && <Badge label={me.role.toUpperCase()} colour={ROLE_COLOURS[me.role] ?? ''} />}
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Session expires</p>
            <p className="text-sm text-slate-100">
              {expiry ? expiry.toLocaleString() : '—'}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Auth method</p>
            <p className="text-sm text-slate-100">JWT Bearer Token</p>
          </div>
        </div>
      </SectionCard>

      <SectionCard title="Role Permissions">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { r: 'admin', perms: ['Manage users', 'Modify policies', 'View all logs', 'Configure alerts', 'Manage integrations', 'Deploy services'] },
            { r: 'developer', perms: ['Test AI endpoints', 'View own logs', 'Read DLP rules', 'Trigger manual scan'] },
            { r: 'auditor', perms: ['View all logs', 'Generate reports', 'Export audit trails', 'Monitor alerts'] },
          ].map(({ r, perms }) => (
            <div key={r} className={`rounded-lg border p-4 ${r === role ? 'border-cyan-500/30 bg-cyan-500/5' : 'border-slate-800 opacity-50'}`}>
              <div className="mb-3">
                <Badge label={r.toUpperCase()} colour={ROLE_COLOURS[r] ?? ''} />
                {r === role && <span className="ml-2 text-[10px] text-cyan-400">← your role</span>}
              </div>
              <ul className="space-y-1">
                {perms.map((p) => (
                  <li key={p} className="text-xs text-slate-400 flex items-center gap-1.5">
                    <span className="text-green-400">✓</span> {p}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="API Key — Machine-to-Machine Access">
        <p className="text-xs text-slate-500 mb-4">
          API keys authenticate server-to-server requests via the{' '}
          <code className="text-cyan-400 bg-slate-800 px-1 rounded">X-API-Key</code> header at{' '}
          <code className="text-cyan-400 bg-slate-800 px-1 rounded">/ai/query/apikey</code>.
          {role !== 'admin' && ' Only admins can generate keys.'}
        </p>

        {role === 'admin' && (
          <>
            <button
              onClick={generateKey}
              disabled={generating}
              className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-900 text-sm font-semibold disabled:opacity-60 transition"
            >
              {generating ? 'Generating…' : 'Generate New API Key'}
            </button>

            {error && <p className="mt-3 text-xs text-red-400">{error}</p>}

            {apiKey && (
              <div className="mt-4 bg-slate-800 border border-slate-700 rounded-lg p-3 flex items-center justify-between gap-3">
                <code className="text-xs text-cyan-300 break-all flex-1">{apiKey}</code>
                <button
                  onClick={copyKey}
                  className="shrink-0 text-xs px-3 py-1.5 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-700 transition"
                >
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
            )}
            {apiKey && (
              <p className="mt-2 text-[11px] text-yellow-400">
                ⚠ Store this key securely — it will not be shown again.
              </p>
            )}
          </>
        )}
      </SectionCard>
    </div>
  );
}

function ModelsTab({ role }: { role: Role }) {
  const [models, setModels] = useState<ModelOption[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch(`${API_BASE}/ai/models`)
      .then((r) => r.ok ? r.json() : null)
      .then((d) => { if (d?.models) setModels(d.models); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const byProvider = models.reduce<Record<string, ModelOption[]>>((acc, m) => {
    if (!acc[m.provider]) acc[m.provider] = [];
    acc[m.provider].push(m);
    return acc;
  }, {});

  const allProviders = ['ollama', 'openai', 'anthropic', 'gemini', 'groq'];
  const activeProviders = Object.keys(byProvider);
  const inactiveProviders = allProviders.filter((p) => !activeProviders.includes(p));

  const providerName: Record<string, string> = {
    ollama: 'Ollama (Local)', openai: 'OpenAI', anthropic: 'Anthropic', gemini: 'Google Gemini', groq: 'Groq',
  };

  return (
    <div>
      <SectionCard title="Active Providers">
        {loading ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : activeProviders.length === 0 ? (
          <p className="text-sm text-slate-500">No models configured.</p>
        ) : (
          <div className="space-y-4">
            {activeProviders.map((provider) => (
              <div key={provider}>
                <div className="flex items-center gap-2 mb-2">
                  <StatusDot on label={providerName[provider] ?? provider} />
                  <Badge label="ACTIVE" colour="text-green-400 bg-green-400/10 border-green-500/20" />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 pl-4">
                  {byProvider[provider].map((m) => (
                    <div key={m.id} className={`rounded-lg border px-3 py-2 flex items-center gap-2 ${PROVIDER_COLOURS[provider] ?? 'border-slate-700'}`}>
                      <span className="text-xs font-medium">{m.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="Unconfigured Providers">
        <p className="text-xs text-slate-500 mb-3">
          Add the corresponding API key to <code className="text-cyan-400 bg-slate-800 px-1 rounded">.env</code> to enable a provider.
        </p>
        <div className="space-y-2">
          {inactiveProviders.map((p) => (
            <div key={p} className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0">
              <StatusDot on={false} label={providerName[p] ?? p} />
              <span className="text-[11px] text-slate-600">No API key configured</span>
            </div>
          ))}
          {inactiveProviders.length === 0 && (
            <p className="text-sm text-green-400">All providers are active.</p>
          )}
        </div>
      </SectionCard>
    </div>
  );
}

function PolicyTab() {
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch(`${API_BASE}/api/settings/overview`)
      .then((r) => r.ok ? r.json() : null)
      .then((d) => d && setData(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-sm text-slate-500 mt-4">Loading…</p>;
  if (!data) return <p className="text-sm text-red-400 mt-4">Failed to load policy data.</p>;

  return (
    <div>
      <SectionCard title="DLP Engine">
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div>
            <p className="text-xs text-slate-500 mb-1">Status</p>
            <StatusDot on={data.dlp.enabled} label={data.dlp.enabled ? 'Enabled' : 'Disabled'} />
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Block on detection</p>
            <StatusDot on={data.dlp.block_on_detection} label={data.dlp.block_on_detection ? 'Yes' : 'No'} />
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Redact mode</p>
            <p className="text-sm text-slate-200 capitalize">{data.dlp.redact_mode}</p>
          </div>
        </div>
        <p className="text-xs text-slate-500 mb-3">Active detection rules</p>
        <div className="space-y-2">
          {data.dlp.rules.map((rule) => (
            <div key={rule.name} className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0">
              <div>
                <p className="text-sm text-slate-200">{rule.name}</p>
                <p className="text-xs text-slate-500">{rule.description}</p>
              </div>
              <Badge label={rule.severity.toUpperCase()} colour={SEVERITY_COLOURS[rule.severity] ?? ''} />
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="Rate Limits">
        <div className="flex items-center gap-2 mb-4">
          <StatusDot on={data.rate_limits.enabled} label={data.rate_limits.enabled ? 'Enabled' : 'Disabled'} />
          <span className="text-xs text-slate-500">· {data.rate_limits.window_seconds}s sliding window</span>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {Object.entries(data.rate_limits.per_role).map(([role, rpm]) => (
            <div key={role} className="bg-slate-800 border border-slate-700 rounded-lg p-4 text-center">
              <Badge label={role.toUpperCase()} colour={ROLE_COLOURS[role] ?? ''} />
              <p className="text-2xl font-bold text-slate-100 mt-2">{rpm.toLocaleString()}</p>
              <p className="text-xs text-slate-500">req / min</p>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="Compliance Frameworks">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          {data.compliance.frameworks.map((fw) => (
            <div key={fw} className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-center">
              <p className="text-sm font-semibold text-cyan-400">{fw}</p>
              <p className="text-[11px] text-green-400 mt-1">Active</p>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
          <div>
            <p className="text-xs text-slate-500 mb-1">Log retention</p>
            <p className="text-sm text-slate-200">{data.compliance.log_retention_days} days</p>
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Encryption standard</p>
            <p className="text-sm text-slate-200">{data.compliance.encryption_standard || '—'}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Audit trail</p>
            <StatusDot on={data.compliance.audit_trail_required} label={data.compliance.audit_trail_required ? 'Required' : 'Optional'} />
          </div>
        </div>
      </SectionCard>
    </div>
  );
}

function SystemTab({ role }: { role: Role }) {
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch(`${API_BASE}/api/settings/overview`)
      .then((r) => r.ok ? r.json() : null)
      .then((d) => d && setData(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (role !== 'admin') return <LockCard tab="System settings" />;
  if (loading) return <p className="text-sm text-slate-500 mt-4">Loading…</p>;
  if (!data) return <p className="text-sm text-red-400 mt-4">Failed to load system data.</p>;

  return (
    <div>
      <SectionCard title="Database Encryption">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p className="text-xs text-slate-500 mb-1">Status</p>
            <StatusDot on={data.encryption.enabled} label={data.encryption.enabled ? 'Enabled' : 'Disabled'} />
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Key ID</p>
            <p className="text-sm text-slate-200">{data.encryption.key_id ?? '—'}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Data in transit</p>
            <StatusDot on label="HTTPS / TLS" />
          </div>
        </div>
        {!data.encryption.enabled && (
          <div className="mt-4 rounded-lg border border-yellow-500/20 bg-yellow-500/5 px-4 py-3">
            <p className="text-xs text-yellow-400">
              Database encryption is disabled. Set <code className="bg-slate-800 px-1 rounded">DB_ENCRYPTION_ENABLED=true</code> in{' '}
              <code className="bg-slate-800 px-1 rounded">.env</code> to enable Fernet encryption on log records.
            </p>
          </div>
        )}
      </SectionCard>

      <SectionCard title="Alert Integrations">
        <p className="text-xs text-slate-500 mb-4">
          Webhooks are configured via environment variables. Alerts fire automatically on DLP blocks, rate limit hits, and auth failures.
        </p>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-slate-800">
            <div className="flex items-center gap-3">
              <StatusDot on={data.integrations.slack} label="Slack" />
            </div>
            <span className="text-xs text-slate-500">
              {data.integrations.slack ? 'SLACK_WEBHOOK_URL configured' : 'Set SLACK_WEBHOOK_URL in .env'}
            </span>
          </div>
          <div className="flex items-center justify-between py-2">
            <div className="flex items-center gap-3">
              <StatusDot on={data.integrations.discord} label="Discord" />
            </div>
            <span className="text-xs text-slate-500">
              {data.integrations.discord ? 'DISCORD_WEBHOOK_URL configured' : 'Set DISCORD_WEBHOOK_URL in .env'}
            </span>
          </div>
        </div>
      </SectionCard>

      <SectionCard title="Gateway Health">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p className="text-xs text-slate-500 mb-1">DLP Middleware</p>
            <StatusDot on label="Running" />
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Rate Limiter</p>
            <StatusDot on label="Running" />
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">RBAC Enforcement</p>
            <StatusDot on label="Running" />
          </div>
        </div>
      </SectionCard>
    </div>
  );
}

// ─── main component ───────────────────────────────────────────────────────────

const TABS = [
  { id: 'profile', label: 'Profile' },
  { id: 'models', label: 'AI Models' },
  { id: 'policy', label: 'DLP & Policy' },
  { id: 'system', label: 'System' },
];

export default function Settings() {
  const [activeTab, setActiveTab] = useState('profile');
  const role = (getRole() ?? 'developer') as Role;

  function renderTab() {
    switch (activeTab) {
      case 'profile': return <ProfileTab role={role} />;
      case 'models': return <ModelsTab role={role} />;
      case 'policy': return <PolicyTab />;
      case 'system': return <SystemTab role={role} />;
      default: return null;
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="mb-6 border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-semibold text-slate-100">Settings</h1>
        <p className="text-sm text-slate-400">Gateway configuration, policy, and account settings</p>
      </div>

      <div className="flex gap-6 flex-1 min-h-0">
        {/* Sidebar */}
        <div className="w-52 shrink-0">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-2">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full text-left px-4 py-2.5 rounded-lg text-sm font-medium transition mb-0.5 ${
                  activeTab === tab.id
                    ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-500/20'
                    : 'text-slate-400 hover:bg-slate-800 border border-transparent'
                }`}
              >
                {tab.label}
                {tab.id === 'system' && role !== 'admin' && (
                  <span className="ml-2 text-[10px] text-slate-600">🔒</span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-h-0 overflow-y-auto">
          {renderTab()}
        </div>
      </div>
    </div>
  );
}
