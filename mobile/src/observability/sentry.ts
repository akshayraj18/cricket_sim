/**
 * Sentry crash/error reporting for the app. No-op unless a DSN is configured
 * (so it stays quiet in local dev unless you opt in). The DSN is a client key,
 * safe to ship in the app bundle; prefer the EXPO_PUBLIC_SENTRY_DSN env var.
 */
import * as Sentry from '@sentry/react-native';

import { setErrorReporter } from '@/components/error-boundary';

const SENTRY_DSN =
  process.env.EXPO_PUBLIC_SENTRY_DSN ??
  'https://13ecce3d8a677ab5a9d4b8a3c4aafa7d@o4511559169146880.ingest.us.sentry.io/4511559175176192';

let initialised = false;

export function initSentry() {
  if (initialised || !SENTRY_DSN) return;
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: __DEV__ ? 'development' : 'production',
    // Don't attach PII (IPs, etc.) by default.
    sendDefaultPii: false,
    // Errors only for now; bump to sample performance traces later.
    tracesSampleRate: 0,
  });
  // Route caught render errors from the top-level boundary into Sentry.
  setErrorReporter((error, componentStack) => {
    Sentry.captureException(error, componentStack ? { extra: { componentStack } } : undefined);
  });
  initialised = true;
}

/** Manually report a handled error (e.g. a failed API call worth tracking). */
export function reportError(error: unknown) {
  if (initialised) Sentry.captureException(error);
}
