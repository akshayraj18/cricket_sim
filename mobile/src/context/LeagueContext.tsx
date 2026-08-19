import { useFocusEffect } from 'expo-router';
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

import { ApiError } from '@/api/client';
import { seasonApi } from '@/api/season';
import { LeaguePayload } from '@/api/types';
import { useCareer } from '@/context/CareerContext';
import { useTour } from '@/context/TourContext';
import { useFunnelTracking } from '@/observability/use-funnel-tracking';

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
  const { activeCareerId, setActiveCareerId } = useCareer();
  const { active: tourActive } = useTour();
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
      // A 404 means this career is gone, not that something went wrong: the
      // guided tour deletes its throwaway demo, a career can be deleted on
      // another device, and the backend's ownership check 404s a career that
      // belongs to a different account. All three leave a stale id pointing at
      // nothing, and surfacing the backend's "Career not found." as an error
      // banner is both alarming and unactionable — the user cannot fix it from
      // that screen. Drop the stale id instead so the app falls back to the
      // no-career state and offers to create or pick one.
      if (err instanceof ApiError && err.status === 404) {
        setPayload(null);
        setActiveCareerId(null);
      } else {
        setError(err instanceof Error ? err.message : 'Failed to load career data');
      }
    } finally {
      setLoading(false);
    }
  }, [activeCareerId, setActiveCareerId]);

  useEffect(() => {
    // During the tour, the tour owns the demo career's payload (it calls
    // setPayload after each state change), so skip the auto-refetch to avoid
    // racing it. Outside the tour, refetch on mount / active-career change.
    if (!tourActive) refresh();
  }, [refresh, tourActive]);

  // Re-sync whenever any tab regains focus, so actions taken on one screen
  // (draft picks, lineup saves, match results) are reflected everywhere else.
  // EXCEPT during the guided tour: the tour drives the demo career's state and
  // sets the payload itself, so a focus refetch here would race and clobber it
  // (e.g. overwriting the just-started draft board with the setup screen).
  useFocusEffect(
    useCallback(() => {
      if (!tourActive) refresh();
    }, [refresh, tourActive])
  );

  // Gameplay funnel events are derived here rather than at each button, since
  // this is where every path (manual, autodraft, quick-sim, auto-sim) converges.
  useFunnelTracking(activeCareerId, payload, tourActive);

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
