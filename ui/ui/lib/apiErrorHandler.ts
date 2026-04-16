export interface ApiErrorResponse {
  detail?: string;
  errors?: string[];
}

/**
 * Centralized frontend error handler.
 * Converts backend responses into safe UI messages.
 */
export async function handleApiError(res: Response): Promise<string> {
  let data: ApiErrorResponse | null = null;

  try {
    data = await res.json();
  } catch {
    // If backend returns non-JSON
    return 'Unexpected server response.';
  }

  // 422 — Validation errors
  if (res.status === 422 && data?.errors) {
    return data.errors.join(' • ');
  }

  // 401 — Unauthorized
  if (res.status === 401) {
    return 'Invalid username or password.';
  }

  // 500 — Internal error (generic from backend)
  if (res.status >= 500) {
    return data?.detail || 'Internal server error.';
  }

  // Any other backend-provided message
  return data?.detail || 'Something went wrong.';
}