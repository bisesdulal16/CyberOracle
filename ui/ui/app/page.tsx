import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* NAV */}
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2">
          <div className="text-xs font-semibold text-sky-500">CyberOracle</div>
          <div className="text-xs font-medium text-slate-500">
            Secure AI Gateway
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/login"
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50"
          >
            Log in
          </Link>

          <Link
            href="/signup"
            className="rounded-lg bg-sky-600 px-3 py-2 text-xs font-medium text-white shadow-sm hover:bg-sky-700"
          >
            Sign up
          </Link>
        </div>
      </header>

      {/* HERO */}
      <main className="mx-auto w-full max-w-6xl px-6 pb-14 pt-10">
        <div className="grid gap-8 lg:grid-cols-2 lg:items-center">
          <div>
            <p className="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-medium text-slate-600">
              AI activity monitoring • DLP • Audit logging • Compliance
            </p>

            <h1 className="mt-4 text-3xl font-semibold leading-tight text-slate-900 sm:text-4xl">
              Secure your AI apps with visibility and guardrails.
            </h1>

            <p className="mt-3 max-w-xl text-sm text-slate-600">
              CyberOracle is a secure AI gateway that detects prompt injection,
              prevents data exfiltration, redacts sensitive output, and produces
              audit-ready compliance reports.
            </p>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Link
                href="/login"
                className="inline-flex items-center justify-center rounded-lg bg-sky-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-sky-700"
              >
                Log in
              </Link>

              <Link
                href="/signup"
                className="inline-flex items-center justify-center rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
              >
                Create account
              </Link>
            </div>

            <p className="mt-4 text-[11px] text-slate-400">
              By using CyberOracle, you acknowledge security monitoring and
              logging of AI activity.
            </p>
          </div>

          {/* FEATURES */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-900">
              Platform highlights
            </h2>

            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <Feature title="Prompt injection defense" />
              <Feature title="DLP & redaction" />
              <Feature title="Audit logs" />
              <Feature title="Compliance mapping" />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function Feature({ title }: { title: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs font-medium text-slate-700">
      {title}
    </div>
  );
}