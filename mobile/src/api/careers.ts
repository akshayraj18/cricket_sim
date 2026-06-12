import { apiClient } from '@/api/client';
import {
  CareerCreateRequest,
  CareerDetail,
  CareerSummary,
  MatchBallsOut,
  MatchDetail,
  MatchSummary,
} from '@/api/types';

export const careersApi = {
  list: () => apiClient.get<CareerSummary[]>('/careers'),

  create: (body: CareerCreateRequest) => apiClient.post<CareerDetail>('/careers', body),

  get: (careerId: string) => apiClient.get<CareerDetail>(`/careers/${careerId}`),

  saveState: (careerId: string, state: Record<string, unknown>) =>
    apiClient.put<CareerDetail>(`/careers/${careerId}/state`, state),

  delete: (careerId: string) => apiClient.delete<void>(`/careers/${careerId}`),

  listMatches: (careerId: string, seasonYear?: number) =>
    apiClient.get<MatchSummary[]>(
      `/careers/${careerId}/matches${seasonYear !== undefined ? `?season_year=${seasonYear}` : ''}`
    ),

  getMatch: (careerId: string, matchId: string) =>
    apiClient.get<MatchDetail>(`/careers/${careerId}/matches/${matchId}`),

  getMatchBalls: (careerId: string, matchId: string) =>
    apiClient.get<MatchBallsOut>(`/careers/${careerId}/matches/${matchId}/balls`),
};
