import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

import { authApi } from '@/api/auth';
import { ApiError, SessionExpiredError } from '@/api/client';
import {
  SocialAuthCancelledError,
  signInWithApple as nativeAppleSignIn,
  signInWithGoogle as nativeGoogleSignIn,
} from '@/api/socialAuth';
import { AuthResponse, UserOut } from '@/api/types';
import { useAnalytics } from '@/observability/analytics';
import {
  clearGuestRefreshToken,
  clearTokens,
  getGuestRefreshToken,
  getTokens,
  setGuestRefreshToken,
  setTokens,
} from '@/api/tokenStorage';

/** A user with no linked provider and no email is an anonymous guest. */
function isGuest(user: UserOut | null): boolean {
  return !!user && !user.has_apple_link && !user.has_google_link && !user.email;
}

type AuthStatus = 'loading' | 'signed-out' | 'signed-in';

interface AuthContextValue {
  status: AuthStatus;
  user: UserOut | null;
  /** True when we have a stored session but couldn't reach the backend to restore it. */
  offline: boolean;
  /** Creates (or resumes) an anonymous guest session. */
  continueAsGuest: () => Promise<void>;
  /** True if the current user is an anonymous guest (no linked provider). */
  isGuest: boolean;
  /** Sign in with Apple (iOS). */
  signInWithApple: () => Promise<void>;
  /** Sign in with Google. */
  signInWithGoogle: () => Promise<void>;
  /** Link Apple to the current (guest) account, keeping its career. iOS only. */
  linkApple: () => Promise<void>;
  /** Link Google to the current (guest) account, keeping its career. */
  linkGoogle: () => Promise<void>;
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
  const analytics = useAnalytics();
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

  const applyAuthResponse = useCallback(
    async ({ user: authedUser, tokens }: AuthResponse, method: 'guest' | 'apple' | 'google') => {
      await setTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
      // Remember a guest's refresh token durably so the account can be resumed
      // after sign-out; a real (linked) account doesn't need this fallback.
      if (isGuest(authedUser)) {
        await setGuestRefreshToken(tokens.refresh_token);
      } else {
        await clearGuestRefreshToken();
      }
      analytics.identify(authedUser.id);
      analytics.capture('signed_in', { method });
      setUser(authedUser);
      setOffline(false);
      setStatus('signed-in');
    },
    [analytics]
  );

  const continueAsGuest = async () => {
    setError(null);
    try {
      // Resume this device's existing guest account if we have its credential,
      // so the guest's career survives a sign-out. Fall back to creating a new
      // guest only if there's no saved one (or it's been revoked/expired).
      const savedGuestToken = await getGuestRefreshToken();
      if (savedGuestToken) {
        try {
          const tokens = await authApi.refresh(savedGuestToken);
          await setTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
          await setGuestRefreshToken(tokens.refresh_token);
          const me = await authApi.me();
          analytics.identify(me.id);
          analytics.capture('signed_in', { method: 'guest' });
          setUser(me);
          setOffline(false);
          setStatus('signed-in');
          return;
        } catch {
          // Saved guest credential is gone/expired — clear it and make a new guest.
          await clearGuestRefreshToken();
        }
      }
      await applyAuthResponse(await authApi.guest(), 'guest');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start guest session');
    }
  };

  const signInWithApple = async () => {
    setError(null);
    try {
      const { token, displayName } = await nativeAppleSignIn();
      await applyAuthResponse(await authApi.apple(token, displayName), 'apple');
    } catch (err) {
      if (err instanceof SocialAuthCancelledError) return;
      setError(err instanceof Error ? err.message : 'Apple sign-in failed');
    }
  };

  const signInWithGoogle = async () => {
    setError(null);
    try {
      const { token, displayName } = await nativeGoogleSignIn();
      await applyAuthResponse(await authApi.google(token, displayName), 'google');
    } catch (err) {
      if (err instanceof SocialAuthCancelledError) return;
      setError(err instanceof Error ? err.message : 'Google sign-in failed');
    }
  };

  // Linking keeps the current session/user (and thus the guest's career) and
  // just attaches a provider, so the account becomes durable and portable.
  const linkApple = async () => {
    setError(null);
    try {
      const { token } = await nativeAppleSignIn();
      const updated = await authApi.linkApple(token);
      await clearGuestRefreshToken();
      analytics.capture('account_linked', { provider: 'apple' });
      setUser(updated);
    } catch (err) {
      if (err instanceof SocialAuthCancelledError) return;
      setError(err instanceof Error ? err.message : 'Linking Apple failed');
    }
  };

  const linkGoogle = async () => {
    setError(null);
    try {
      const { token } = await nativeGoogleSignIn();
      const updated = await authApi.linkGoogle(token);
      await clearGuestRefreshToken();
      analytics.capture('account_linked', { provider: 'google' });
      setUser(updated);
    } catch (err) {
      if (err instanceof SocialAuthCancelledError) return;
      setError(err instanceof Error ? err.message : 'Linking Google failed');
    }
  };

  const retry = useCallback(async () => {
    setStatus('loading');
    await restoreSession();
  }, [restoreSession]);

  const signOut = async () => {
    await clearTokens();
    analytics.capture('signed_out');
    analytics.reset();
    setUser(null);
    setOffline(false);
    setStatus('signed-out');
  };

  const value = useMemo(
    () => ({
      status,
      user,
      offline,
      isGuest: isGuest(user),
      continueAsGuest,
      signInWithApple,
      signInWithGoogle,
      linkApple,
      linkGoogle,
      retry,
      signOut,
      error,
    }),
    [status, user, offline, retry, error]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
