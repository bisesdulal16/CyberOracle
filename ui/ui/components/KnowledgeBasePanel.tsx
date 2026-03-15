'use client';

import React, { useState } from 'react';

type Article = {
  id: string;
  title: string;
  content: React.ReactNode;
};

const ARTICLES: Article[] = [
  {
    id: 'overview',
    title: 'What is CyberOracle?',
    content: (
      <div className="space-y-3 text-sm text-slate-300 leading-relaxed">
        <p>
          <strong className="text-slate-100">CyberOracle</strong> is a Secure AI
          Gateway and Compliance Automation Platform. It acts as a defensive
          middleware layer that sits between your applications and any AI/LLM
          service — intercepting every request, scanning for sensitive data,
          enforcing compliance policies, and producing a complete audit trail.
        </p>
        <p>
          Every prompt sent to an AI model passes through CyberOracle first.
          If the prompt contains sensitive information (SSNs, credit card
          numbers, API keys, email addresses), it is either{' '}
          <strong className="text-slate-100">redacted</strong> before reaching the model or{' '}
          <strong className="text-slate-100">blocked</strong> entirely, depending on the configured policy.
          The model&apos;s response undergoes the same scan before being returned
          to the caller.
        </p>
        <p>
          CyberOracle logs every event to a structured, encrypted audit trail
          and fires alerts when high-risk activity is detected — giving security
          teams full visibility over AI usage across the organization.
        </p>
        <div className="rounded-lg bg-cyan-400/5 border border-cyan-500/20 px-4 py-3 mt-2">
          <p className="font-semibold text-cyan-300 mb-1">Capstone I scope</p>
          <p className="text-cyan-400/80">
            LLM backend: Ollama (fully local — no external API calls). All
            processing stays on your machine during development.
          </p>
        </div>
      </div>
    ),
  },
  {
    id: 'architecture',
    title: 'How it works — Architecture',
    content: (
      <div className="space-y-4 text-sm text-slate-300 leading-relaxed">
        <p>
          CyberOracle is built on a FastAPI backend, a PostgreSQL database, and a
          Next.js dashboard. A Prometheus + Loki + Grafana stack provides
          deep observability.
        </p>
        <pre className="rounded-lg border border-slate-700 bg-slate-800 p-4 font-mono text-[11px] text-cyan-300 leading-6 overflow-x-auto">
{`Browser / App
    ↓  POST /ai/query {prompt}
Rate Limiter middleware
    ↓
DLP Filter middleware (input scan)
    ↓  BLOCK if critical PII detected
    ↓  REDACT and continue otherwise
Ollama LLM  (local)
    ↓  raw response
DLP Filter middleware (output scan)
    ↓  BLOCK / REDACT / ALLOW
Structured logger → PostgreSQL (encrypted)
    ↓
Alert Manager → Discord / Slack  (on high-risk events)
    ↓
Response returned to caller`}
        </pre>
        <p>
          The <strong className="text-slate-100">Circuit Breaker</strong> pattern wraps the Ollama client —
          if the model is unavailable, requests fail fast rather than piling up.
          A <strong className="text-slate-100">Model Router</strong> abstracts the LLM provider so future
          models (OpenAI, Anthropic, etc.) can be added as adapters.
        </p>
      </div>
    ),
  },
  {
    id: 'dlp',
    title: 'What CyberOracle blocks — DLP Rules',
    content: (
      <div className="space-y-4 text-sm text-slate-300 leading-relaxed">
        <p>
          CyberOracle uses two DLP layers in series: a fast regex engine and an
          advanced NLP engine (Microsoft Presidio).
        </p>

        <h3 className="text-xs font-semibold text-slate-200 mt-2">
          Regex DLP — Pattern matching
        </h3>
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-slate-800 text-left">
              <th className="px-3 py-2 border border-slate-700 font-semibold text-slate-300">Pattern</th>
              <th className="px-3 py-2 border border-slate-700 font-semibold text-slate-300">Severity</th>
              <th className="px-3 py-2 border border-slate-700 font-semibold text-slate-300">Example</th>
            </tr>
          </thead>
          <tbody>
            {[
              ['Social Security Number (SSN)', 'Critical', '123-45-6789'],
              ['Credit / debit card number', 'Critical', '4111 1111 1111 1111'],
              ['Exposed API key / token', 'High', 'api_key="AbCdEf123…"'],
              ['Email address', 'Medium', 'user@example.com'],
            ].map(([pattern, sev, ex]) => (
              <tr key={pattern} className="border-b border-slate-700/50">
                <td className="px-3 py-2 border border-slate-700/50 text-slate-300">{pattern}</td>
                <td className="px-3 py-2 border border-slate-700/50">
                  <span
                    className={
                      sev === 'Critical'
                        ? 'text-red-400 font-semibold'
                        : sev === 'High'
                          ? 'text-amber-400 font-semibold'
                          : 'text-blue-400 font-semibold'
                    }
                  >
                    {sev}
                  </span>
                </td>
                <td className="px-3 py-2 border border-slate-700/50 font-mono text-slate-400">
                  {ex}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <h3 className="text-xs font-semibold text-slate-200 mt-4">
          Presidio DLP — NLP entity recognition
        </h3>
        <p>
          Microsoft Presidio detects over 50 PII entity types including names,
          addresses, phone numbers, passport numbers, and medical terms. It runs
          after the regex layer and can anonymize detected entities by replacing
          them with type labels (e.g.{' '}
          <code className="font-mono text-xs bg-slate-800 rounded px-1 text-cyan-300">&lt;PERSON&gt;</code>
          ).
        </p>

        <h3 className="text-xs font-semibold text-slate-200 mt-4">
          Policy decisions
        </h3>
        <div className="space-y-2">
          {[
            ['Allow', 'emerald', 'No sensitive data detected — request proceeds unchanged.'],
            ['Redact', 'amber', 'Sensitive patterns detected but below block threshold — values are masked before reaching the model.'],
            ['Block', 'red', 'Critical PII detected — request is stopped and an alert is fired. Caller receives a policy violation message.'],
          ].map(([label, color, desc]) => (
            <div key={label as string} className="flex gap-3 items-start">
              <span
                className={`mt-0.5 shrink-0 text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                  color === 'emerald'
                    ? 'bg-emerald-400/10 text-emerald-400 border border-emerald-500/20'
                    : color === 'amber'
                      ? 'bg-amber-400/10 text-amber-400 border border-amber-500/20'
                      : 'bg-red-400/10 text-red-400 border border-red-500/20'
                }`}
              >
                {label}
              </span>
              <p className="text-slate-400">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    ),
  },
  {
    id: 'compliance',
    title: 'Compliance frameworks',
    content: (
      <div className="space-y-4 text-sm text-slate-300 leading-relaxed">
        <p>
          CyberOracle maps its security controls to four major compliance
          frameworks. The Compliance panel gives a live per-control status view.
        </p>
        {[
          {
            name: 'HIPAA',
            desc: 'Health Insurance Portability and Accountability Act. CyberOracle enforces PHI detection via DLP, audit logging, Fernet encryption at rest, and rate limiting. Current coverage: 80%.',
          },
          {
            name: 'FERPA',
            desc: 'Family Educational Rights and Privacy Act. Student PII is detected and redacted by Presidio. Access controls map to the RBAC roles defined in policy.yaml. Current coverage: 85%.',
          },
          {
            name: 'NIST CSF',
            desc: 'NIST Cybersecurity Framework. CyberOracle addresses Identify, Protect, Detect, and Respond functions through threat modeling, DLP, structured logging, and alerting. Current coverage: 82%.',
          },
          {
            name: 'GDPR',
            desc: 'General Data Protection Regulation. Data minimization is enforced via the DLP redaction layer. Audit trails support the right to erasure and data subject requests. Current coverage: 73%.',
          },
        ].map((f) => (
          <div
            key={f.name}
            className="rounded-lg border border-slate-800 bg-slate-800 p-4"
          >
            <p className="font-semibold text-slate-100 mb-1">{f.name}</p>
            <p className="text-slate-400">{f.desc}</p>
          </div>
        ))}
        <p className="text-slate-500">
          Gap areas (RBAC enforcement, n8n workflows) are tracked in the
          Compliance panel and will be closed in Capstone II.
        </p>
      </div>
    ),
  },
  {
    id: 'rbac',
    title: 'Access control — RBAC roles',
    content: (
      <div className="space-y-4 text-sm text-slate-300 leading-relaxed">
        <p>
          CyberOracle defines three RBAC roles in{' '}
          <code className="font-mono text-xs bg-slate-800 rounded px-1 text-cyan-300">
            docs/threat-modeling/policy.yaml
          </code>
          . Role claims are embedded in the JWT access token issued at login.
        </p>
        {[
          {
            role: 'Admin',
            color: 'text-red-400 bg-red-400/10 border-red-500/20',
            desc: 'Full platform access. Can manage users, modify DLP rules, deploy services, view all logs, and configure alerts.',
          },
          {
            role: 'Developer',
            color: 'text-cyan-400 bg-cyan-400/10 border-cyan-500/20',
            desc: "Restricted access for API testing and DLP monitoring. Can call AI endpoints, trigger manual scans, and view dashboards. Cannot view other users' logs.",
          },
          {
            role: 'Auditor',
            color: 'text-violet-400 bg-violet-400/10 border-violet-500/20',
            desc: 'Read-only compliance view. Can view all logs, generate reports, export audit trails, and monitor alerts. Cannot modify any settings.',
          },
        ].map((r) => (
          <div key={r.role} className={`rounded-lg border p-4 ${r.color}`}>
            <p className="font-semibold mb-1">{r.role}</p>
            <p className="text-slate-400">{r.desc}</p>
          </div>
        ))}
        <div className="rounded-lg bg-amber-400/5 border border-amber-500/20 px-4 py-3">
          <p className="font-semibold text-amber-400 mb-1">Capstone I status</p>
          <p className="text-amber-300/80">
            The RBAC dependency module is implemented in{' '}
            <code className="font-mono text-[11px] bg-slate-800 rounded px-1 text-cyan-300">app/auth/rbac.py</code> and
            wired to selected endpoints. Full enforcement across all routes
            requires the frontend login flow to send JWT tokens — planned for
            Capstone II.
          </p>
        </div>
      </div>
    ),
  },
  {
    id: 'alerting',
    title: 'Alerting & incident response',
    content: (
      <div className="space-y-4 text-sm text-slate-300 leading-relaxed">
        <p>
          CyberOracle fires alerts when high-risk events are detected. Alerts
          are dispatched via the{' '}
          <code className="font-mono text-xs bg-slate-800 rounded px-1 text-cyan-300">
            alert_manager.py
          </code>{' '}
          utility.
        </p>

        <h3 className="text-xs font-semibold text-slate-200">Alert triggers</h3>
        <div className="space-y-2">
          {[
            ['PII Detection (block)', 'Critical', 'Fired when a request is blocked due to sensitive data. Notifies Admin + Auditor.'],
            ['Rate Limit Exceeded', 'Warning', 'Fired when a client exceeds the configured requests-per-minute. Notifies Admin + Developer.'],
            ['Failed Authentication (×5)', 'High', 'Fired after 5 consecutive auth failures from the same source. Notifies Admin + Auditor.'],
          ].map(([name, sev, desc]) => (
            <div key={name as string} className="rounded-lg border border-slate-800 bg-slate-800 p-3">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-semibold text-slate-200">{name}</span>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                    sev === 'Critical'
                      ? 'bg-red-400/10 text-red-400 border border-red-500/20'
                      : sev === 'High'
                        ? 'bg-amber-400/10 text-amber-400 border border-amber-500/20'
                        : 'bg-blue-400/10 text-blue-400 border border-blue-500/20'
                  }`}
                >
                  {sev}
                </span>
              </div>
              <p className="text-slate-400">{desc}</p>
            </div>
          ))}
        </div>

        <h3 className="text-xs font-semibold text-slate-200 mt-2">
          Notification channels
        </h3>
        <div className="space-y-2">
          <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-800 p-3">
            <span className="font-semibold text-slate-200 w-20 shrink-0">Discord</span>
            <span className="text-slate-400">
              Configured via{' '}
              <code className="font-mono text-xs bg-slate-900 rounded px-1 text-cyan-300">DISCORD_WEBHOOK_URL</code>{' '}
              in{' '}
              <code className="font-mono text-xs bg-slate-900 rounded px-1 text-cyan-300">.env</code>.
              Leave blank in development to disable.
            </span>
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-800 p-3">
            <span className="font-semibold text-slate-200 w-20 shrink-0">Slack</span>
            <span className="text-slate-400">
              Configured via{' '}
              <code className="font-mono text-xs bg-slate-900 rounded px-1 text-cyan-300">SLACK_WEBHOOK_URL</code>{' '}
              in{' '}
              <code className="font-mono text-xs bg-slate-900 rounded px-1 text-cyan-300">.env</code>.
              Uses Slack Incoming Webhooks API.
            </span>
          </div>
        </div>
      </div>
    ),
  },
  {
    id: 'api',
    title: 'API quick reference',
    content: (
      <div className="space-y-3 text-sm text-slate-300">
        <p>
          All endpoints are served at{' '}
          <code className="font-mono text-xs bg-slate-800 rounded px-1 text-cyan-300">http://localhost:8000</code>{' '}
          by default.
        </p>
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-slate-800 text-left">
              <th className="px-3 py-2 border border-slate-700 font-semibold text-slate-300">Method</th>
              <th className="px-3 py-2 border border-slate-700 font-semibold text-slate-300">Path</th>
              <th className="px-3 py-2 border border-slate-700 font-semibold text-slate-300">Description</th>
            </tr>
          </thead>
          <tbody>
            {[
              ['GET',  '/health',                    'Service health check'],
              ['POST', '/ai/query',                  'Secure AI gateway — DLP + Ollama'],
              ['POST', '/api/scan',                  'Standalone DLP scan'],
              ['POST', '/api/documents/sanitize',    'PDF/DOCX upload + DLP redaction'],
              ['GET',  '/api/metrics/summary',       'Dashboard summary (24h)'],
              ['GET',  '/api/compliance/status',     'Compliance control coverage'],
              ['GET',  '/api/alerts/recent',         'Recent high-severity alerts'],
              ['GET',  '/logs/list',                 'Paginated audit log with filters'],
              ['GET',  '/api/reports/summary',       'Aggregated stats for date range'],
              ['POST', '/auth/login',                'Issue JWT access token'],
            ].map(([method, path, desc]) => (
              <tr key={path} className="border-b border-slate-700/50 hover:bg-slate-800 transition">
                <td className="px-3 py-2 border border-slate-700/50">
                  <span
                    className={`font-mono font-semibold ${
                      method === 'POST' ? 'text-cyan-400' : 'text-emerald-400'
                    }`}
                  >
                    {method}
                  </span>
                </td>
                <td className="px-3 py-2 border border-slate-700/50 font-mono text-slate-300">
                  {path}
                </td>
                <td className="px-3 py-2 border border-slate-700/50 text-slate-400">{desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-slate-500">
          Full interactive docs:{' '}
          <code className="font-mono text-xs bg-slate-800 rounded px-1 text-cyan-300">
            http://localhost:8000/docs
          </code>
        </p>
      </div>
    ),
  },
];

const KnowledgeBasePanel: React.FC = () => {
  const [activeId, setActiveId] = useState(ARTICLES[0].id);

  const active = ARTICLES.find((a) => a.id === activeId) ?? ARTICLES[0];

  return (
    <div className="mt-4">
      <div className="mb-5">
        <h1 className="text-2xl font-semibold text-slate-100">Knowledge Base</h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Security and product documentation — how CyberOracle works and what it
          protects against.
        </p>
      </div>

      <div className="flex gap-5">
        {/* Left nav */}
        <aside className="w-52 shrink-0 space-y-0.5 bg-slate-900 border border-slate-800 rounded-xl p-2">
          {ARTICLES.map((article) => (
            <button
              key={article.id}
              onClick={() => setActiveId(article.id)}
              className={
                'w-full text-left px-3 py-2 text-xs font-medium transition rounded-lg ' +
                (activeId === article.id
                  ? 'border-l-2 border-cyan-400 bg-cyan-400/10 text-cyan-400 rounded-l-none pl-2.5'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200')
              }
            >
              {article.title}
            </button>
          ))}
        </aside>

        {/* Content */}
        <article className="flex-1 bg-slate-900 border border-slate-800 rounded-xl p-6 min-h-[400px]">
          <h2 className="text-base font-semibold text-slate-100 mb-4">
            {active.title}
          </h2>
          {active.content}
        </article>
      </div>
    </div>
  );
};

export default KnowledgeBasePanel;
