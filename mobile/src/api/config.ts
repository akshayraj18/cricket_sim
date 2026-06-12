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
