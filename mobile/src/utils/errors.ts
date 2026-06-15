import { ApiError, SessionExpiredError } from '@/api/client';

/**
 * Turn any thrown error into a user-facing { title, message } pair with
 * actionable guidance. Used by the global error popup so network blips,
 * server errors, and validation failures all read clearly instead of
 * surfacing a raw "TypeError: Network request failed" (or nothing at all).
 */
export interface UserFacingError {
  title: string;
  message: string;
  /** Whether the action is worth retrying (network/5xx) vs. a hard failure. */
  retryable: boolean;
}

/** A bare `fetch` rejection (no connection / server unreachable) is a TypeError. */
function isNetworkError(err: unknown): boolean {
  return (
    err instanceof TypeError &&
    /network request failed|failed to fetch|network error/i.test(err.message)
  );
}

export function getUserFacingError(err: unknown): UserFacingError {
  if (isNetworkError(err)) {
    return {
      title: 'No connection',
      message: "We couldn't reach the server. Check your internet connection and try again.",
      retryable: true,
    };
  }

  if (err instanceof SessionExpiredError) {
    return {
      title: 'Signed out',
      message: 'Your session expired. Please sign in again to continue.',
      retryable: false,
    };
  }

  if (err instanceof ApiError) {
    // 5xx — the server failed; retrying often works (e.g. backend restarting).
    if (err.status >= 500) {
      return {
        title: 'Something went wrong',
        message: 'The server ran into a problem. Please try again in a moment.',
        retryable: true,
      };
    }
    // 4xx — usually a validation message worth showing verbatim.
    return {
      title: 'Unable to continue',
      message: err.message || 'That action could not be completed. Please try again.',
      retryable: err.status === 408 || err.status === 429,
    };
  }

  return {
    title: 'Something went wrong',
    message: err instanceof Error && err.message ? err.message : 'An unexpected error occurred. Please try again.',
    retryable: true,
  };
}
