import Link from 'next/link';
import {
  ShieldCheckIcon,
  MagnifyingGlassIcon,
  ClipboardDocumentListIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import type { ReactNode } from 'react';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-slate-950">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2">
          <ShieldCheckIcon className="w-4 h-4 text-cyan-400" />
          <div className="text-xs font-semibold text-cyan-400">CyberOracle</div>
          <div className="text-xs font-medium text-slate-500">Secure AI Gateway</div>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/login"
            className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-medium text-slate-200 hover:bg-slate-700 transition"
          >
            Log in
          </Link>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl px-6 pb-14 pt-10">
        <div className="grid gap-8 lg:grid-cols-2 lg:items-center">
          <div>
            <p className="inline-flex items-center rounded-full border border-slate-800 bg-slate-800 px-3 py-1 text-[11px] font-medium text-slate-400">
              AI activity monitoring · DLP · Audit logging · Compliance
            </p>
            <h1 className="mt-4 text-3xl font-semibold leading-tight text-slate-100 sm:text-4xl">
              Secure your AI apps with visibility and guardrails.
            </h1>
            <p className="mt-3 max-w-xl text-sm text-slate-400">
              CyberOracle is a secure AI gateway that detects prompt injection,
              prevents data exfiltration, redacts sensitive output, and produces
              audit-ready compliance reports.
            </p>
            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Link
                href="/login"
                className="inline-flex items-center justify-center rounded-lg bg-cyan-500 hover:bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-slate-900 transition"
              >
                Log in
              </Link>
            </div>
            <p className="mt-4 text-[11px] text-slate-500">
              By using CyberOracle, you acknowledge security monitoring and
              logging of AI activity.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <h2 className="text-sm font-semibold text-slate-200">Platform highlights</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <Feature
                icon={<ShieldCheckIcon className="w-4 h-4 text-cyan-400" />}
                title="Prompt injection defense"
                description="DLP scans all inputs before reaching the model."
              />
              <Feature
                icon={<MagnifyingGlassIcon className="w-4 h-4 text-cyan-400" />}
                title="DLP & redaction"
                description="SSN, card, API key, and email detection with auto-redact."
              />
              <Feature
                icon={<ClipboardDocumentListIcon className="w-4 h-4 text-cyan-400" />}
                title="Audit logs"
                description="Every AI request logged and encrypted in PostgreSQL."
              />
              <Feature
                icon={<ChartBarIcon className="w-4 h-4 text-cyan-400" />}
                title="Compliance mapping"
                description="HIPAA, FERPA, NIST CSF, and GDPR control tracking."
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function Feature({
  icon,
  title,
  description,
}: {
  icon: ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800 p-4">
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <span className="text-xs font-semibold text-slate-200">{title}</span>
      </div>
      <p className="text-[11px] text-slate-400">{description}</p>
    </div>
  );
}
