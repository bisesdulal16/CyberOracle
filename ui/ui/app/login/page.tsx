'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { saveAuth } from '../../lib/auth';
import { ShieldCheckIcon } from '@heroicons/react/24/outline';

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

      if (res.status === 422) {
        setError('Invalid input. Username may only contain letters, numbers, hyphens, underscores, and dots.');
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
      setError('Cannot reach the backend. Make sure CyberOracle is running.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <div className="w-full max-w-md bg-slate-900 rounded-2xl border border-slate-800 p-8">
        <div className="mb-6 text-center">
          <div className="flex items-center justify-center gap-1.5 mb-2">
            <ShieldCheckIcon className="w-5 h-5 text-cyan-400" />
            <span className="text-sm font-semibold text-cyan-400">CyberOracle</span>
          </div>
          <h1 className="mt-1 text-xl font-semibold text-slate-100">
            Sign in to Secure AI Gateway
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Access your AI security dashboard, logs, and compliance reports.
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-xs text-red-400">
            {error}
          </div>
        )}

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-1">
            <label
              htmlFor="username"
              className="block text-xs font-medium text-slate-400"
            >
              Username
            </label>
            <input
              id="username"
              type="text"
              required
              autoComplete="username"
              maxLength={100}
              value={username}
              onChange={(e) => setUsername(e.target.value.replace(/[^a-zA-Z0-9_\-\.]/g, ''))}
              className="block w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition"
              placeholder="admin"
            />
            <p className="text-[10px] text-slate-500 mt-1">
              Letters, numbers, hyphens, underscores and dots only.
            </p>
          </div>

          <div className="space-y-1">
            <label
              htmlFor="password"
              className="block text-xs font-medium text-slate-400"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              maxLength={128}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="block w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-2 inline-flex w-full items-center justify-center rounded-lg bg-cyan-500 hover:bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-slate-900 disabled:opacity-60 disabled:cursor-not-allowed transition"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="mt-5 text-[11px] text-center text-slate-500">
          By signing in you agree to CyberOracle&apos;s security monitoring and
          logging of AI activity.
        </p>
      </div>
    </div>
  );
}