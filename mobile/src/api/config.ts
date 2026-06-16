import Constants from 'expo-constants';
import { Platform } from 'react-native';

/**
 * Resolve the FastAPI base URL for dev/prod.
 *
 * - In production, set EXPO_PUBLIC_API_URL at build time.
 * - In dev, Android emulators can't reach the host via `localhost`, so we
 *   fall back to the Metro dev server host (10.0.2.2 maps to host on the
 *   Android emulator).
 */
function resolveApiUrl(): string {
  const fromEnv = process.env.EXPO_PUBLIC_API_URL;
  if (fromEnv) return fromEnv;

  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000';
  }

  const hostUri = Constants.expoConfig?.hostUri;
  if (hostUri) {
    const host = hostUri.split(':')[0];
    return `http://${host}:8000`;
  }

  return 'http://localhost:8000';
}

export const API_URL = resolveApiUrl();

/**
 * Google Sign-In OAuth client IDs (from Google Cloud Console, project
 * "cric-sim"). Prefer `EXPO_PUBLIC_GOOGLE_*` env vars; the inline fallbacks
 * are placeholders for local dev — replace them with the real IDs.
 *
 * - `webClientId`: the Web OAuth client ID. This is the audience the backend
 *   verifies the returned idToken against, so it MUST match the backend's
 *   `google_client_ids`.
 * - `iosClientId`: the iOS OAuth client ID (its reverse is the
 *   `iosUrlScheme` in app.json).
 */
export const GOOGLE_WEB_CLIENT_ID =
  process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID ??
  '474477947414-jb0fkhakmtdctplqmk9rlno8bguke6al.apps.googleusercontent.com';
export const GOOGLE_IOS_CLIENT_ID =
  process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID ??
  '474477947414-bff512hqin1s695shti2nic0dg1t31hk.apps.googleusercontent.com';

/**
 * PostHog product-analytics project key + host (US Cloud). The project token is
 * a write-only client key, safe to ship in the app; prefer the
 * EXPO_PUBLIC_POSTHOG_* env vars. Leave the key blank to disable analytics.
 */
export const POSTHOG_API_KEY =
  process.env.EXPO_PUBLIC_POSTHOG_API_KEY ?? 'phc_mUVAzBYQqHVXXdApccNhYQMjGJQukhUmaJDviG9o53Rp';
export const POSTHOG_HOST = process.env.EXPO_PUBLIC_POSTHOG_HOST ?? 'https://us.i.posthog.com';

/**
 * Public URLs for the legal documents, shown in the account sheet and required
 * by the app stores. Set the real hosted URLs at deploy time via the
 * EXPO_PUBLIC_*_URL env vars (e.g. a GitHub Pages or marketing-site page).
 */
export const PRIVACY_POLICY_URL =
  process.env.EXPO_PUBLIC_PRIVACY_POLICY_URL ?? 'https://akshayraj18.github.io/cricket_sim/privacy-policy';
export const TERMS_URL =
  process.env.EXPO_PUBLIC_TERMS_URL ?? 'https://akshayraj18.github.io/cricket_sim/terms';
