import { apiClient } from '@/api/client';
import {
  AggressionActionBody,
  ImpactSubActionBody,
  LineupActionBody,
  LiveMatchPayload,
  MatchCompleteResponse,
  NextBatterActionBody,
  PlayOverActionBody,
  SuperOverLineupActionBody,
  TossActionBody,
} from '@/api/types';

const base = (careerId: string) => `/careers/${careerId}/match`;

export const liveMatchApi = {
  get: (careerId: string) => apiClient.get<LiveMatchPayload>(base(careerId)),

  begin: (careerId: string) => apiClient.post<LiveMatchPayload>(`${base(careerId)}/begin`),

  complete: (careerId: string) =>
    apiClient.post<MatchCompleteResponse>(`${base(careerId)}/complete`),

  toss: (careerId: string, body: TossActionBody) =>
    apiClient.post<LiveMatchPayload>(`${base(careerId)}/toss`, body),

  setLineup: (careerId: string, body: LineupActionBody) =>
    apiClient.post<LiveMatchPayload>(`${base(careerId)}/lineup`, body),

  playOver: (careerId: string, body: PlayOverActionBody = {}) =>
    apiClient.post<LiveMatchPayload>(`${base(careerId)}/play-over`, body),

  playBall: (careerId: string, body: PlayOverActionBody = {}) =>
    apiClient.post<LiveMatchPayload>(`${base(careerId)}/play-ball`, body),

  playUntil: (careerId: string, body: PlayOverActionBody = {}) =>
    apiClient.post<LiveMatchPayload>(`${base(careerId)}/play-until`, body),

  setAggression: (careerId: string, body: AggressionActionBody) =>
    apiClient.post<LiveMatchPayload>(`${base(careerId)}/aggression`, body),

  selectNextBatter: (careerId: string, body: NextBatterActionBody) =>
    apiClient.post<LiveMatchPayload>(`${base(careerId)}/next-batter`, body),

  setSuperOverLineup: (careerId: string, body: SuperOverLineupActionBody) =>
    apiClient.post<LiveMatchPayload>(`${base(careerId)}/super-over-lineup`, body),

  applyImpactSub: (careerId: string, body: ImpactSubActionBody) =>
    apiClient.post<LiveMatchPayload>(`${base(careerId)}/impact-sub`, body),

  // Test-only actions
  proceedSession: (careerId: string) =>
    apiClient.post<LiveMatchPayload>(`${base(careerId)}/proceed-session`, {}),

  followOnDecision: (careerId: string, enforce: boolean) =>
    apiClient.post<LiveMatchPayload>(`${base(careerId)}/follow-on-decision`, { enforce }),

  declare: (careerId: string) =>
    apiClient.post<LiveMatchPayload>(`${base(careerId)}/declare`, {}),
};
