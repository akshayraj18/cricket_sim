import { createContext, useCallback, useContext, useMemo, type ReactNode } from 'react';
import { Alert } from 'react-native';

import { SessionExpiredError } from '@/api/client';
import { reportError } from '@/observability/sentry';
import { getUserFacingError } from '@/utils/errors';

/**
 * App-wide error surfacing. `showError` turns any thrown error into a native
 * alert popup with a friendly message and guidance ("Please try again"), and
 * reports it to Sentry. Pass an `onRetry` to add a "Try Again" button that
 * re-runs the failed action for retryable errors (network blips, 5xx).
 */
interface ShowErrorOptions {
  /** Re-run the failed action; shown as "Try Again" for retryable errors. */
  onRetry?: () => void;
}

interface ErrorContextValue {
  showError: (err: unknown, options?: ShowErrorOptions) => void;
}

const ErrorContext = createContext<ErrorContextValue | null>(null);

export function ErrorProvider({ children }: { children: ReactNode }) {
  const showError = useCallback((err: unknown, options?: ShowErrorOptions) => {
    // A session-expiry is handled by the auth flow (it bounces to sign-in);
    // a popup on top of that is just noise.
    if (err instanceof SessionExpiredError) return;

    reportError(err);
    const { title, message, retryable } = getUserFacingError(err);

    const buttons =
      retryable && options?.onRetry
        ? [
            { text: 'Cancel', style: 'cancel' as const },
            { text: 'Try Again', onPress: options.onRetry },
          ]
        : [{ text: 'OK' }];

    Alert.alert(title, message, buttons);
  }, []);

  const value = useMemo(() => ({ showError }), [showError]);

  return <ErrorContext.Provider value={value}>{children}</ErrorContext.Provider>;
}

export function useError(): ErrorContextValue {
  const ctx = useContext(ErrorContext);
  if (!ctx) throw new Error('useError must be used within an ErrorProvider');
  return ctx;
}
