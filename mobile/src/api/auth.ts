import { apiClient } from '@/api/client';
import { AuthResponse, TokenPair, UserOut } from '@/api/types';

export const authApi = {
  guest: () => apiClient.post<AuthResponse>('/auth/guest', undefined, { skipAuth: true }),

  apple: (identityToken: string, displayName?: string) =>
    apiClient.post<AuthResponse>(
      '/auth/apple',
      { identity_token: identityToken, display_name: displayName },
      { skipAuth: true }
    ),

  google: (idToken: string, displayName?: string) =>
    apiClient.post<AuthResponse>(
      '/auth/google',
      { id_token: idToken, display_name: displayName },
      { skipAuth: true }
    ),

  linkApple: (identityToken: string) =>
    apiClient.post<UserOut>('/auth/link/apple', { identity_token: identityToken }),

  linkGoogle: (idToken: string) => apiClient.post<UserOut>('/auth/link/google', { id_token: idToken }),

  refresh: (refreshToken: string) =>
    apiClient.post<TokenPair>('/auth/refresh', { refresh_token: refreshToken }, { skipAuth: true }),

  me: () => apiClient.get<UserOut>('/auth/me'),

  /** Permanently delete the current account and all its data. Irreversible. */
  deleteAccount: () => apiClient.delete<void>('/auth/me'),
};
