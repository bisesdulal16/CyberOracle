/**
 * CyberOracle — Unified API Client
 *
 * Provides a consistent way to make authenticated requests to the CyberOracle backend.
 * All requests automatically include the JWT Bearer token when available.
 */

import { getToken } from './auth';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

/**
 * Make an authenticated API request
 * @param endpoint - API endpoint path (e.g., '/api/metrics/summary')
 * @param options - Fetch options
 * @returns Promise resolving to the response
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();

  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...(options.headers as Record<string, string> | undefined ?? {}),
    },
  });

  if (response.status === 401) {
    // Clear auth and redirect to login
    window.location.replace('/login');
    throw new Error('Unauthorized - please log in again');
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error (${response.status}): ${errorText}`);
  }

  return response.json() as Promise<T>;
}

/**
 * Health check endpoint
 * @returns Promise resolving to health status
 */
export async function healthCheck(): Promise<{ status: string; service: string }> {
  return apiRequest('/health');
}

/**
 * Login endpoint
 * @param username - User's username
 * @param password - User's password
 * @returns Promise resolving to auth token and role
 */
export async function login(username: string, password: string): Promise<{
  access_token: string;
  role: string
}> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  if (response.status === 401) {
    throw new Error('Invalid username or password');
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Login failed: ${errorText}`);
  }

  return response.json();
}

/**
 * Get dashboard summary
 * @returns Promise resolving to summary metrics
 */
export async function getDashboardSummary(): Promise<{
  total_prompts_24h: number;
  blocked_prompts: number;
  redacted_outputs: number;
  high_risk_events: number;
}> {
  return apiRequest('/api/metrics/summary');
}

/**
 * Get compliance status
 * @returns Promise resolving to compliance data
 */
export async function getComplianceStatus(): Promise<{
  compliance_score: number;
  compliant_controls: number;
  total_controls: number;
}> {
  return apiRequest('/api/compliance/status');
}

/**
 * Get recent alerts
 * @returns Promise resolving to alert list
 */
export async function getRecentAlerts(): Promise<{
  alerts: Array<{
    id: string;
    type: string;
    severity: string;
    message: string;
    timestamp: string;
  }>;
}> {
  return apiRequest('/api/alerts/recent');
}