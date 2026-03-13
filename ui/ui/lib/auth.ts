/**
 * CyberOracle — Client-side auth utilities
 *
 * Stores the JWT access token and role in localStorage.
 * Provides an apiFetch() wrapper that automatically attaches
 * the Bearer token and redirects to /login on HTTP 401.
 *
 * Usage
 * -----
 *   import { apiFetch, saveAuth, clearAuth, isAuthenticated, getRole } from '../lib/auth';
 */

const TOKEN_KEY = 'co_token';
const ROLE_KEY = 'co_role';

// ---------------------------------------------------------------------------
// Storage helpers
// ---------------------------------------------------------------------------

/** Persist auth state after a successful login. */
export function saveAuth(token: string, role: string): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(ROLE_KEY, role);
}

/** Return the stored JWT, or null if not present. */
export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

/** Return the stored role ("admin" | "developer" | "auditor"), or null. */
export function getRole(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ROLE_KEY);
}

/** Remove auth state (called on logout or 401). */
export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
}

/** True if a token is currently stored. */
export function isAuthenticated(): boolean {
  return !!getToken();
}

// ---------------------------------------------------------------------------
// Authenticated fetch wrapper
// ---------------------------------------------------------------------------

/**
 * Drop-in replacement for fetch() that:
 *  - Attaches `Authorization: Bearer <token>` when a token is stored.
 *  - Redirects to /login and clears auth on HTTP 401.
 *
 * All other behaviour (error handling, response parsing) is left to the caller,
 * identical to the standard fetch API.
 */
export async function apiFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  const token = getToken();

  const merged: RequestInit = {
    ...init,
    headers: {
      ...(init?.headers as Record<string, string> | undefined ?? {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  };

  const response = await fetch(input, merged);

  if (response.status === 401) {
    clearAuth();
    // Full redirect — the current page is abandoned and the user lands on login
    window.location.replace('/login');
  }

  return response;
}
