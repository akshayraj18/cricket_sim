import { useFocusEffect } from 'expo-router';
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

import { seasonApi } from '@/api/season';
import { LeaguePayload } from '@/api/types';
import { useCareer } from '@/context/CareerContext';

interface LeagueContextValue {
  payload: LeaguePayload | null;
  loading: boolean;
  error: string | null;
  /** Refetches the payload from the server. */
  refresh: () => Promise<void>;
  /** Applies an optimistic payload (e.g. immediately after an action response) without a network round-trip. */
  setPayload: (payload: LeaguePayload) => void;
}

const LeagueContext = createContext<LeagueContextValue | null>(null);

export function LeagueProvider({ children }: { children: ReactNode }) {
  const { activeCareerId } = useCareer();
  const [payload, setPayload] = useState<LeaguePayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!activeCareerId) {
      setPayload(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await seasonApi.getPayload(activeCareerId);
      setPayload(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load career data');
    } finally {
      setLoading(false);
    }
  }, [activeCareerId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Re-sync whenever any tab regains focus, so actions taken on one screen
  // (draft picks, lineup saves, match results) are reflected everywhere else.
  useFocusEffect(
    useCallback(() => {
      refresh();
    }, [refresh])
  );

  const value = useMemo(
    () => ({ payload, loading, error, refresh, setPayload }),
    [payload, loading, error, refresh]
  );

  return <LeagueContext.Provider value={value}>{children}</LeagueContext.Provider>;
}

export function useLeague(): LeagueContextValue {
  const ctx = useContext(LeagueContext);
  if (!ctx) throw new Error('useLeague must be used within a LeagueProvider');
  return ctx;
}
