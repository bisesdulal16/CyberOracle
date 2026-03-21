'use client';

import React, { useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

type FieldErrors = {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
};

export default function SignupPage() {
  const router = useRouter();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [agree, setAgree] = useState(false);

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  const canSubmit = useMemo(() => {
    return (
      name.trim().length > 0 &&
      email.trim().length > 0 &&
      password.length > 0 &&
      confirmPassword.length > 0 &&
      agree &&
      !loading
    );
  }, [name, email, password, confirmPassword, agree, loading]);

  function validate(): FieldErrors {
    const next: FieldErrors = {};

    if (!name.trim()) next.name = 'Please enter your name.';

    // Basic email check (browser also enforces with type=email)
    if (!email.trim()) {
      next.email = 'Please enter a work email.';
    } else if (!/^\S+@\S+\.\S+$/.test(email.trim())) {
      next.email = 'Please enter a valid email address.';
    }

    // Basic password rules (adjust later)
    if (password.length < 8) {
      next.password = 'Password must be at least 8 characters.';
    }

    if (confirmPassword !== password) {
      next.confirmPassword = 'Passwords do not match.';
    }

    if (!agree) {
      // not a field error; handled inline
    }

    return next;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitError(null);

    const nextErrors = validate();
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) return;
    if (!agree) return;

    setLoading(true);

    try {
      // TODO: Replace with real backend call, e.g. POST /api/auth/signup
      // For now, simulate success and route to dashboard.
      await new Promise((res) => setTimeout(res, 700));
      router.push('/dashboard');
    } catch (err) {
      setSubmitError('Something went wrong creating your account. Please try again.');
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
            Create your account
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Get access to your AI security dashboard, logs, and compliance reports.
          </p>
        </div>

        {submitError && (
          <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
            {submitError}
          </div>
        )}

        <form className="space-y-4" onSubmit={handleSubmit} noValidate>
          {/* Name */}
          <div className="space-y-1">
            <label htmlFor="name" className="block text-xs font-medium text-slate-700">
              Full name
            </label>
            <input
              id="name"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={
                'block w-full rounded-lg border px-3 py-2 text-sm text-slate-900 shadow-sm focus:outline-none focus:ring-1 ' +
                (errors.name
                  ? 'border-rose-300 focus:ring-rose-400 focus:border-rose-400'
                  : 'border-slate-200 focus:ring-sky-500 focus:border-sky-500')
              }
              placeholder="Jane Doe"
            />
            {errors.name && <p className="text-[11px] text-rose-600">{errors.name}</p>}
          </div>

          {/* Email */}
          <div className="space-y-1">
            <label htmlFor="email" className="block text-xs font-medium text-slate-700">
              Work email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={
                'block w-full rounded-lg border px-3 py-2 text-sm text-slate-900 shadow-sm focus:outline-none focus:ring-1 ' +
                (errors.email
                  ? 'border-rose-300 focus:ring-rose-400 focus:border-rose-400'
                  : 'border-slate-200 focus:ring-sky-500 focus:border-sky-500')
              }
              placeholder="you@company.com"
              autoComplete="email"
            />
            {errors.email && <p className="text-[11px] text-rose-600">{errors.email}</p>}
          </div>

          {/* Password */}
          <div className="space-y-1">
            <label htmlFor="password" className="block text-xs font-medium text-slate-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={
                'block w-full rounded-lg border px-3 py-2 text-sm text-slate-900 shadow-sm focus:outline-none focus:ring-1 ' +
                (errors.password
                  ? 'border-rose-300 focus:ring-rose-400 focus:border-rose-400'
                  : 'border-slate-200 focus:ring-sky-500 focus:border-sky-500')
              }
              placeholder="••••••••"
              autoComplete="new-password"
            />
            <p className="text-[11px] text-slate-400">
              Use 8+ characters. (You can enforce stronger rules later.)
            </p>
            {errors.password && (
              <p className="text-[11px] text-rose-600">{errors.password}</p>
            )}
          </div>

          {/* Confirm Password */}
          <div className="space-y-1">
            <label
              htmlFor="confirmPassword"
              className="block text-xs font-medium text-slate-700"
            >
              Confirm password
            </label>
            <input
              id="confirmPassword"
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className={
                'block w-full rounded-lg border px-3 py-2 text-sm text-slate-900 shadow-sm focus:outline-none focus:ring-1 ' +
                (errors.confirmPassword
                  ? 'border-rose-300 focus:ring-rose-400 focus:border-rose-400'
                  : 'border-slate-200 focus:ring-sky-500 focus:border-sky-500')
              }
              placeholder="••••••••"
              autoComplete="new-password"
            />
            {errors.confirmPassword && (
              <p className="text-[11px] text-rose-600">{errors.confirmPassword}</p>
            )}
          </div>

          {/* Agreement */}
          <div className="flex items-start gap-2 text-xs">
            <input
              id="agree"
              type="checkbox"
              checked={agree}
              onChange={(e) => setAgree(e.target.checked)}
              className="mt-0.5 h-3 w-3 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
            />
            <label htmlFor="agree" className="text-slate-600">
              I agree to CyberOracle&apos;s security monitoring and logging of AI activity.
            </label>
          </div>

          <button
            type="submit"
            disabled={!canSubmit}
            className="mt-2 inline-flex w-full items-center justify-center rounded-lg bg-sky-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-sky-700 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <div className="mt-6 flex items-center justify-between text-xs">
          <Link href="/" className="text-slate-500 hover:text-slate-700">
            ← Back to home
          </Link>

          <Link href="/login" className="text-sky-600 hover:text-sky-700">
            Already have an account? Sign in
          </Link>
        </div>

        <p className="mt-6 text-[11px] text-center text-slate-400">
          This is a mock signup flow for now. Backend auth will be integrated later.
        </p>
      </div>
    </div>
  );
}