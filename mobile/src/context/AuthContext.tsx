import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

import { authApi } from '@/api/auth';
import { UserOut } from '@/api/types';
import { clearTokens, getTokens, setTokens } from '@/api/tokenStorage';

type AuthStatus = 'loading' | 'signed-out' | 'signed-in';

interface AuthContextValue {
  status: AuthStatus;
  user: UserOut | null;
  /** Creates (or resumes) an anonymous guest session. */
  continueAsGuest: () => Promise<void>;
  signOut: () => Promise<void>;
  error: string | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [user, setUser] = useState<UserOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const tokens = await getTokens();
      if (!tokens) {
        setStatus('signed-out');
        return;
      }

      try {
        const me = await authApi.me();
        setUser(me);
        setStatus('signed-in');
      } catch {
        await clearTokens();
        setStatus('signed-out');
      }
    })();
  }, []);

  const continueAsGuest = async () => {
    setError(null);
    try {
      const { user: guestUser, tokens } = await authApi.guest();
      await setTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
      setUser(guestUser);
      setStatus('signed-in');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start guest session');
    }
  };

  const signOut = async () => {
    await clearTokens();
    setUser(null);
    setStatus('signed-out');
  };

  const value = useMemo(
    () => ({ status, user, continueAsGuest, signOut, error }),
    [status, user, error]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
