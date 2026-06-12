import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const ACCESS_TOKEN_KEY = 'cricket_sim.access_token';
const REFRESH_TOKEN_KEY = 'cricket_sim.refresh_token';
// A guest account has no password, so its refresh token is the only way back
// into it. We stash it under a separate key that signOut does NOT clear, so a
// guest can sign out and later resume the SAME account (and its career) via
// "Continue as Guest" instead of getting a fresh, empty guest.
const GUEST_REFRESH_TOKEN_KEY = 'cricket_sim.guest_refresh_token';

export interface TokenPair {
  accessToken: string;
  refreshToken: string;
}

// expo-secure-store has no web implementation; fall back to AsyncStorage there.
async function getItem(key: string): Promise<string | null> {
  if (Platform.OS === 'web') return AsyncStorage.getItem(key);
  return SecureStore.getItemAsync(key);
}

async function setItem(key: string, value: string): Promise<void> {
  if (Platform.OS === 'web') return AsyncStorage.setItem(key, value);
  return SecureStore.setItemAsync(key, value);
}

async function deleteItem(key: string): Promise<void> {
  if (Platform.OS === 'web') return AsyncStorage.removeItem(key);
  return SecureStore.deleteItemAsync(key);
}

export async function getTokens(): Promise<TokenPair | null> {
  const [accessToken, refreshToken] = await Promise.all([
    getItem(ACCESS_TOKEN_KEY),
    getItem(REFRESH_TOKEN_KEY),
  ]);

  if (!accessToken || !refreshToken) return null;
  return { accessToken, refreshToken };
}

export async function setTokens(tokens: TokenPair): Promise<void> {
  await Promise.all([
    setItem(ACCESS_TOKEN_KEY, tokens.accessToken),
    setItem(REFRESH_TOKEN_KEY, tokens.refreshToken),
  ]);
}

export async function clearTokens(): Promise<void> {
  await Promise.all([deleteItem(ACCESS_TOKEN_KEY), deleteItem(REFRESH_TOKEN_KEY)]);
}

/** Remember this device's guest refresh token so the guest account can be resumed later. */
export async function setGuestRefreshToken(refreshToken: string): Promise<void> {
  await setItem(GUEST_REFRESH_TOKEN_KEY, refreshToken);
}

export async function getGuestRefreshToken(): Promise<string | null> {
  return getItem(GUEST_REFRESH_TOKEN_KEY);
}

/** Forget the saved guest credential — e.g. once the guest links a real account. */
export async function clearGuestRefreshToken(): Promise<void> {
  await deleteItem(GUEST_REFRESH_TOKEN_KEY);
}
