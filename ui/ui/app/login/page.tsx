'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { saveAuth } from '../../lib/auth';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (res.status === 401) {
        setError('Invalid username or password.');
        return;
      }

      if (!res.ok) {
        setError('Login failed — backend unavailable. Please try again.');
        return;
      }

      const data = await res.json();
      saveAuth(data.access_token, data.role);
      router.replace('/dashboard');
    } catch {
      setError('Cannot reach the backend. Make sure CyberOracle is running on port 8000.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
        <div className="mb-6 text-center">
          <div className="text-xs font-semibold text-sky-500">CyberOracle</div>
          <h1 className="mt-1 text-xl font-semibold text-slate-900">
            Sign in to Secure AI Gateway
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Access your AI security dashboard, logs, and compliance reports.
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-700">
            {error}
          </div>
        )}

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-1">
            <label
              htmlFor="username"
              className="block text-xs font-medium text-slate-700"
            >
              Username
            </label>
            <input
              id="username"
              type="text"
              required
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="block w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 shadow-sm focus:outline-none focus:ring-1 focus:ring-sky-500 focus:border-sky-500"
              placeholder="admin"
            />
          </div>

          <div className="space-y-1">
            <label
              htmlFor="password"
              className="block text-xs font-medium text-slate-700"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="block w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 shadow-sm focus:outline-none focus:ring-1 focus:ring-sky-500 focus:border-sky-500"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-2 inline-flex w-full items-center justify-center rounded-lg bg-sky-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-sky-700 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div className="mt-5 rounded-lg border border-slate-100 bg-slate-50 px-4 py-3 text-[11px] text-slate-500 space-y-1">
          <p className="font-medium text-slate-600">Default credentials</p>
          <p><span className="font-mono">admin</span> / <span className="font-mono">changeme_admin</span> — full access</p>
          <p><span className="font-mono">developer</span> / <span className="font-mono">changeme_dev</span> — API access</p>
          <p><span className="font-mono">auditor</span> / <span className="font-mono">changeme_auditor</span> — read-only</p>
          <p className="text-slate-400 pt-1">Set your own credentials via env vars — see HANDOFF.md Section 9.</p>
        </div>

        <p className="mt-5 text-[11px] text-center text-slate-400">
          By signing in you agree to CyberOracle&apos;s security monitoring and
          logging of AI activity.
        </p>
      </div>
    </div>
  );
}
