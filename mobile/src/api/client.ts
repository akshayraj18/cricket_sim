import { API_URL } from '@/api/config';
import { clearTokens, getTokens, setTokens } from '@/api/tokenStorage';

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/** Raised when the refresh token is invalid/expired and the user must sign in again. */
export class SessionExpiredError extends Error {
  constructor() {
    super('Session expired');
    this.name = 'SessionExpiredError';
  }
}

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const tokens = await getTokens();
  if (!tokens) return null;

  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: tokens.refreshToken }),
  });

  if (!res.ok) {
    // Only a definitive auth rejection (401/403) means the refresh token is
    // actually invalid — clear it so the user re-authenticates. A transient
    // server error (5xx, e.g. backend restarting) must NOT wipe a valid
    // session, or the user's careers would appear to vanish on a blip.
    if (res.status === 401 || res.status === 403) {
      await clearTokens();
      return null;
    }
    throw new ApiError(res.status, `Token refresh failed (${res.status})`);
  }

  const data = await res.json();
  await setTokens({ accessToken: data.access_token, refreshToken: data.refresh_token });
  return data.access_token as string;
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  /** Skip attaching the Authorization header (used for /auth/guest etc). */
  skipAuth?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, skipAuth = false } = options;

  const headers: Record<string, string> = { 'Content-Type': 'application/json' };

  if (!skipAuth) {
    const tokens = await getTokens();
    if (tokens) headers.Authorization = `Bearer ${tokens.accessToken}`;
  }

  let res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && !skipAuth) {
    refreshPromise ??= refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
    const newAccessToken = await refreshPromise;

    if (!newAccessToken) {
      throw new SessionExpiredError();
    }

    res = await fetch(`${API_URL}${path}`, {
      method,
      headers: { ...headers, Authorization: `Bearer ${newAccessToken}` },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  if (!res.ok) {
    let message = res.statusText;
    try {
      const data = await res.json();
      message = data.detail ?? message;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(res.status, message);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'POST', body }),
  put: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'PUT', body }),
  delete: <T>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'DELETE' }),
};
