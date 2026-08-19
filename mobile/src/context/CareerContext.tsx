import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';

import { careersApi } from '@/api/careers';
import { CareerSummary } from '@/api/types';
import { useAuth } from '@/context/AuthContext';

const LEGACY_CAREER_KEY = 'cricket_sim.active_career_id';

function careerKey(userId: string) {
  return `cricket_sim.active_career_id.${userId}`;
}

interface CareerContextValue {
  activeCareerId: string | null;
  activeCareer: CareerSummary | null;
  loading: boolean;
  setActiveCareerId: (careerId: string | null) => void;
  refreshActiveCareer: () => Promise<void>;
}

const CareerContext = createContext<CareerContextValue | null>(null);

export function CareerProvider({ children }: { children: ReactNode }) {
  const { status, user } = useAuth();
  const userId = user?.id ?? null;
  const [activeCareerId, setActiveCareerIdState] = useState<string | null>(null);
  const [activeCareer, setActiveCareer] = useState<CareerSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const prevStatusRef = useRef<string | null>(null);

  useEffect(() => {
    const prevStatus = prevStatusRef.current;
    prevStatusRef.current = status;

    if (status === 'signed-out') {
      // Clear in-memory career state immediately so tabs don't show stale data.
      setActiveCareerIdState(null);
      setActiveCareer(null);
      setLoading(false);
      return;
    }

    if (status !== 'signed-in') {
      setLoading(false);
      return;
    }

    (async () => {
      if (!userId) {
        setLoading(false);
        return;
      }
      const key = careerKey(userId);
      let stored = await AsyncStorage.getItem(key);

      // One-time migration: on the first sign-in after this update, move any
      // value from the old global key into the per-user key, then delete it.
      if (!stored && prevStatus !== 'signed-in') {
        const legacy = await AsyncStorage.getItem(LEGACY_CAREER_KEY);
        if (legacy) {
          stored = legacy;
          await AsyncStorage.setItem(key, legacy);
          await AsyncStorage.removeItem(LEGACY_CAREER_KEY);
        }
      }

      // Assign unconditionally, including when this user has no stored career.
      // Only setting it when `stored` is truthy leaks the previous account's
      // career whenever the user id changes WITHOUT passing through
      // 'signed-out' — account linking, or a refresh resolving to a different
      // user — because the old id would simply stay in state. Signing out and
      // back in is already safe (the branch above clears), but that is the only
      // path that was, and this is the privacy bug in KNOWN_ISSUES.
      setActiveCareerIdState(stored ?? null);
      // The cached summary belongs to whoever was signed in before; drop it and
      // let refreshActiveCareer() refetch for this user.
      if (!stored) setActiveCareer(null);
      setLoading(false);
    })();
  }, [status, userId]);

  const setActiveCareerId = useCallback(
    (careerId: string | null) => {
      setActiveCareerIdState(careerId);
      if (!userId) return;
      const key = careerKey(userId);
      if (careerId) {
        AsyncStorage.setItem(key, careerId);
      } else {
        AsyncStorage.removeItem(key);
      }
    },
    [userId]
  );

  const refreshActiveCareer = useCallback(async () => {
    if (!activeCareerId) {
      setActiveCareer(null);
      return;
    }
    try {
      const career = await careersApi.get(activeCareerId);
      setActiveCareer(career);
    } catch {
      // Career may have been deleted; clear the selection.
      setActiveCareerId(null);
      setActiveCareer(null);
    }
  }, [activeCareerId, setActiveCareerId]);

  useEffect(() => {
    refreshActiveCareer();
  }, [refreshActiveCareer]);

  const value = useMemo(
    () => ({ activeCareerId, activeCareer, loading, setActiveCareerId, refreshActiveCareer }),
    [activeCareerId, activeCareer, loading, setActiveCareerId, refreshActiveCareer]
  );

  return <CareerContext.Provider value={value}>{children}</CareerContext.Provider>;
}

export function useCareer(): CareerContextValue {
  const ctx = useContext(CareerContext);
  if (!ctx) throw new Error('useCareer must be used within a CareerProvider');
  return ctx;
}
