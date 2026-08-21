import { API_URL } from '@/api/config';
import { clearTokens, getTokens, setTokens } from '@/api/tokenStorage';

export class ApiError extends Error {
  status: number;
  /** Per-item problems, when the server rejects with a structured list (e.g. a
   *  roster import naming every invalid row). */
  details?: string[];

  constructor(status: number, message: string, details?: string[]) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

/** Raised when the refresh token is invalid/expired and the user must sign in again. */
export class SessionExpiredError extends Error {
  constructor() {
    super('Session expired');
    this.name = 'SessionExpiredError';
  }
}

/** Raised when a request exceeds REQUEST_TIMEOUT_MS (e.g. no/stalled network). */
export class TimeoutError extends Error {
  constructor() {
    super('The request timed out. Please check your connection and try again.');
    this.name = 'TimeoutError';
  }
}

/** How long to wait before giving up on a request so the UI never hangs forever. */
const REQUEST_TIMEOUT_MS = 15000;

/**
 * `fetch` with a hard timeout. A dropped/stalled connection can otherwise leave
 * a request pending indefinitely, freezing screens like "Quick Sim" in their
 * loading state. On timeout we abort the request and throw a TimeoutError.
 */
async function fetchWithTimeout(input: string, init: RequestInit = {}): Promise<Response> {
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, REQUEST_TIMEOUT_MS);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } catch (err) {
    // An abort can surface as a DOMException("AbortError") or — on React
    // Native — a plain Error with a message like "Aborted" / "Fetch request
    // has been canceled". If it was our timeout firing, report it as such.
    if (timedOut || isAbortError(err)) throw new TimeoutError();
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

/** Detect an abort/cancellation across the shapes RN and the DOM can throw. */
function isAbortError(err: unknown): boolean {
  if (err instanceof DOMException && err.name === 'AbortError') return true;
  if (err instanceof Error) {
    return err.name === 'AbortError' || /abort|fetch request has been canceled|cancell?ed/i.test(err.message);
  }
  return false;
}

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const tokens = await getTokens();
  if (!tokens) return null;

  const res = await fetchWithTimeout(`${API_URL}/auth/refresh`, {
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
  /** Parse the response as text rather than JSON (used for the CSV export). */
  responseType?: 'json' | 'text';
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, skipAuth = false } = options;

  const headers: Record<string, string> = { 'Content-Type': 'application/json' };

  if (!skipAuth) {
    const tokens = await getTokens();
    if (tokens) headers.Authorization = `Bearer ${tokens.accessToken}`;
  }

  let res = await fetchWithTimeout(`${API_URL}${path}`, {
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

    res = await fetchWithTimeout(`${API_URL}${path}`, {
      method,
      headers: { ...headers, Authorization: `Bearer ${newAccessToken}` },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  if (!res.ok) {
    let message = res.statusText;
    let details: string[] | undefined;
    try {
      const data = await res.json();
      const detail = data.detail;
      if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
        // Structured rejection, e.g. a roster import that lists every bad row.
        // Stringifying the object here would show the user "[object Object]".
        message = typeof detail.message === 'string' ? detail.message : message;
        if (Array.isArray(detail.errors)) details = detail.errors.map(String);
      } else if (typeof detail === 'string') {
        message = detail;
      }
    } catch {
      // response had no JSON body
    }
    throw new ApiError(res.status, message, details);
  }

  if (res.status === 204) return undefined as T;
  if (options.responseType === 'text') return (await res.text()) as T;
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
