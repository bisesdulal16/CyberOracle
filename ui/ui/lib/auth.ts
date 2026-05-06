/**
 * CyberOracle — Client-side auth utilities
 *
 * Stores JWT and role in localStorage.
 * Provides apiFetch() wrapper with Bearer token attachment.
 * Proactively detects token expiry to prevent silent failures.
 * Redirects to /login on HTTP 401 or expired token.
 *
 * OWASP API2: Broken Authentication
 */

const TOKEN_KEY = 'co_token';
const ROLE_KEY  = 'co_role';

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
// Token expiry helpers
// ---------------------------------------------------------------------------

/**
 * Decode JWT payload without verifying signature.
 * Used client-side only to read expiry for UX warnings.
 * Signature verification is always done server-side.
 */
export function getTokenExpiry(): Date | null {
  const token = getToken();
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (!payload.exp) return null;
    return new Date(payload.exp * 1000);
  } catch {
    return null;
  }
}

/**
 * Returns true if token expires within the next 5 minutes.
 * Used to show a "session expiring soon" warning in the UI.
 */
export function isTokenExpiringSoon(): boolean {
  const expiry = getTokenExpiry();
  if (!expiry) return false;
  const fiveMinutes = 5 * 60 * 1000;
  return expiry.getTime() - Date.now() < fiveMinutes;
}

/**
 * Returns true if token is already expired.
 */
export function isTokenExpired(): boolean {
  const expiry = getTokenExpiry();
  if (!expiry) return true;
  return expiry.getTime() < Date.now();
}

// ---------------------------------------------------------------------------
// Authenticated fetch wrapper
// ---------------------------------------------------------------------------

/**
 * Drop-in replacement for fetch() that:
 *  - Proactively redirects to /login if token is already expired
 *  - Attaches Authorization: Bearer <token> to every request
 *  - Redirects to /login and clears auth on HTTP 401
 *  - Passes 429 through so components handle rate limit countdowns
 */
export async function apiFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  // Proactively catch expired tokens before making the request
  // Prevents confusing "Failed to fetch" errors in the UI
  if (isTokenExpired()) {
    clearAuth();
    window.location.replace('/login');
    return new Response(null, { status: 401 });
  }

  const token = getToken();

  const merged: RequestInit = {
    ...init,
    headers: {
      ...(init?.headers as Record<string, string> | undefined ?? {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  };

  const response = await fetch(input, merged);

  // Server-side rejection — clear auth and redirect
  if (response.status === 401) {
    clearAuth();
    window.location.replace('/login');
  }

  // 429 passed through — individual components handle countdowns
  return response;
}