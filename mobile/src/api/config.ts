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
