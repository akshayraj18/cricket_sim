/**
 * Native social sign-in helpers (Apple, Google). Each returns the provider's
 * verifiable token + optional display name, which the caller forwards to the
 * backend (`/auth/apple`, `/auth/google`) for signature verification and
 * account creation/linking. Keeping the native SDK calls here isolates the
 * platform-specific bits from `AuthContext`.
 */
import * as AppleAuthentication from 'expo-apple-authentication';
import {
  GoogleSignin,
  isErrorWithCode,
  isSuccessResponse,
  statusCodes,
} from '@react-native-google-signin/google-signin';
import { Platform } from 'react-native';

import { GOOGLE_IOS_CLIENT_ID, GOOGLE_WEB_CLIENT_ID } from '@/api/config';

export class SocialAuthCancelledError extends Error {
  constructor() {
    super('Sign-in cancelled');
    this.name = 'SocialAuthCancelledError';
  }
}

export interface SocialAuthResult {
  token: string;
  displayName?: string;
}

/** Whether Sign in with Apple is usable on this device (iOS 13+ only). */
export async function isAppleSignInAvailable(): Promise<boolean> {
  if (Platform.OS !== 'ios') return false;
  return AppleAuthentication.isAvailableAsync();
}

export async function signInWithApple(): Promise<SocialAuthResult> {
  try {
    const credential = await AppleAuthentication.signInAsync({
      requestedScopes: [
        AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
        AppleAuthentication.AppleAuthenticationScope.EMAIL,
      ],
    });

    if (!credential.identityToken) {
      throw new Error('Apple did not return an identity token.');
    }

    // Apple only returns the name on the very first sign-in; stitch it into a
    // display name when present so the account gets a friendly label.
    const name = [credential.fullName?.givenName, credential.fullName?.familyName]
      .filter(Boolean)
      .join(' ')
      .trim();

    return { token: credential.identityToken, displayName: name || undefined };
  } catch (err) {
    if (err instanceof Error && 'code' in err && (err as { code?: string }).code === 'ERR_REQUEST_CANCELED') {
      throw new SocialAuthCancelledError();
    }
    throw err;
  }
}

let googleConfigured = false;

function configureGoogle() {
  if (googleConfigured) return;
  GoogleSignin.configure({
    webClientId: GOOGLE_WEB_CLIENT_ID,
    iosClientId: GOOGLE_IOS_CLIENT_ID,
  });
  googleConfigured = true;
}

export async function signInWithGoogle(): Promise<SocialAuthResult> {
  configureGoogle();
  try {
    await GoogleSignin.hasPlayServices();
    const response = await GoogleSignin.signIn();

    if (!isSuccessResponse(response)) {
      // User dismissed the picker.
      throw new SocialAuthCancelledError();
    }

    const { idToken, user } = response.data;
    if (!idToken) {
      throw new Error('Google did not return an ID token.');
    }

    return { token: idToken, displayName: user.name ?? undefined };
  } catch (err) {
    if (isErrorWithCode(err) && err.code === statusCodes.SIGN_IN_CANCELLED) {
      throw new SocialAuthCancelledError();
    }
    throw err;
  }
}
