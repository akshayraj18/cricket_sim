import { apiClient } from '@/api/client';
import { LeadershipRequest, LeaguePayload, PresetsRequest, RetentionRequest } from '@/api/types';

const base = (careerId: string) => `/careers/${careerId}`;

export const seasonApi = {
  getPayload: (careerId: string) => apiClient.get<LeaguePayload>(`${base(careerId)}/payload`),

  startDraft: (careerId: string) => apiClient.post<LeaguePayload>(`${base(careerId)}/draft/start`),

  draftPick: (careerId: string, playerName: string) =>
    apiClient.post<LeaguePayload>(`${base(careerId)}/draft/pick`, { player_name: playerName }),

  autodraft: (careerId: string, mode: 'user' | 'all' = 'user') =>
    apiClient.post<LeaguePayload>(`${base(careerId)}/draft/autodraft`, { mode }),

  setLeadership: (careerId: string, body: LeadershipRequest) =>
    apiClient.post<LeaguePayload>(`${base(careerId)}/leadership`, body),

  setPresets: (careerId: string, body: PresetsRequest) =>
    apiClient.post<LeaguePayload>(`${base(careerId)}/presets`, body),

  /** Rename a team or player in this career (the roster editor). */
  rename: (careerId: string, kind: 'team' | 'player', oldName: string, newName: string) =>
    apiClient.post<LeaguePayload>(`${base(careerId)}/rename`, {
      kind,
      old_name: oldName,
      new_name: newName,
    }),

  simulateRound: (careerId: string) =>
    apiClient.post<LeaguePayload>(`${base(careerId)}/season/simulate-round`),

  startPlayoffs: (careerId: string) =>
    apiClient.post<LeaguePayload>(`${base(careerId)}/season/start-playoffs`),

  openRetention: (careerId: string) =>
    apiClient.post<LeaguePayload>(`${base(careerId)}/retention/open`),

  submitRetentions: (careerId: string, body: RetentionRequest) =>
    apiClient.post<LeaguePayload>(`${base(careerId)}/retention`, body),
};
