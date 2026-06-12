import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

import { authApi } from '@/api/auth';
import { ApiError, SessionExpiredError } from '@/api/client';
import {
  SocialAuthCancelledError,
  signInWithApple as nativeAppleSignIn,
  signInWithGoogle as nativeGoogleSignIn,
} from '@/api/socialAuth';
import { AuthResponse, UserOut } from '@/api/types';
import { clearTokens, getTokens, setTokens } from '@/api/tokenStorage';

type AuthStatus = 'loading' | 'signed-out' | 'signed-in';

interface AuthContextValue {
  status: AuthStatus;
  user: UserOut | null;
  /** True when we have a stored session but couldn't reach the backend to restore it. */
  offline: boolean;
  /** Creates (or resumes) an anonymous guest session. */
  continueAsGuest: () => Promise<void>;
  /** Sign in with Apple (iOS). */
  signInWithApple: () => Promise<void>;
  /** Sign in with Google. */
  signInWithGoogle: () => Promise<void>;
  /** Retry restoring a stored session (e.g. after the backend comes back). */
  retry: () => Promise<void>;
  signOut: () => Promise<void>;
  error: string | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * Whether `err` means the stored session is definitively invalid (so we should
 * clear it and sign out) rather than a transient outage (backend down, no
 * network) where we should keep the tokens and let the user retry. A wiped
 * session destroyed on a flaky connection is exactly how a guest's careers
 * appear to "vanish" on reload, so we only clear on real auth failures.
 */
function isAuthFailure(err: unknown): boolean {
  if (err instanceof SessionExpiredError) return true;
  // 401/403 that survived the client's refresh attempt = bad credentials.
  if (err instanceof ApiError) return err.status === 401 || err.status === 403;
  return false;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [user, setUser] = useState<UserOut | null>(null);
  const [offline, setOffline] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const restoreSession = useCallback(async () => {
    const tokens = await getTokens();
    if (!tokens) {
      setOffline(false);
      setStatus('signed-out');
      return;
    }

    try {
      const me = await authApi.me();
      setUser(me);
      setOffline(false);
      setStatus('signed-in');
    } catch (err) {
      if (isAuthFailure(err)) {
        // The stored session is genuinely invalid — drop it.
        await clearTokens();
        setOffline(false);
        setStatus('signed-out');
      } else {
        // Backend unreachable / network error: keep the tokens so the session
        // survives, and mark offline so the UI can offer a retry.
        setOffline(true);
        setStatus('signed-out');
      }
    }
  }, []);

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  const applyAuthResponse = useCallback(async ({ user: authedUser, tokens }: AuthResponse) => {
    await setTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
    setUser(authedUser);
    setOffline(false);
    setStatus('signed-in');
  }, []);

  const continueAsGuest = async () => {
    setError(null);
    try {
      await applyAuthResponse(await authApi.guest());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start guest session');
    }
  };

  const signInWithApple = async () => {
    setError(null);
    try {
      const { token, displayName } = await nativeAppleSignIn();
      await applyAuthResponse(await authApi.apple(token, displayName));
    } catch (err) {
      if (err instanceof SocialAuthCancelledError) return;
      setError(err instanceof Error ? err.message : 'Apple sign-in failed');
    }
  };

  const signInWithGoogle = async () => {
    setError(null);
    try {
      const { token, displayName } = await nativeGoogleSignIn();
      await applyAuthResponse(await authApi.google(token, displayName));
    } catch (err) {
      if (err instanceof SocialAuthCancelledError) return;
      setError(err instanceof Error ? err.message : 'Google sign-in failed');
    }
  };

  const retry = useCallback(async () => {
    setStatus('loading');
    await restoreSession();
  }, [restoreSession]);

  const signOut = async () => {
    await clearTokens();
    setUser(null);
    setOffline(false);
    setStatus('signed-out');
  };

  const value = useMemo(
    () => ({ status, user, offline, continueAsGuest, signInWithApple, signInWithGoogle, retry, signOut, error }),
    [status, user, offline, retry, error]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
