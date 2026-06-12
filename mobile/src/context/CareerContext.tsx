import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { careersApi } from '@/api/careers';
import { CareerSummary } from '@/api/types';
import { useAuth } from '@/context/AuthContext';

const ACTIVE_CAREER_KEY = 'cricket_sim.active_career_id';

interface CareerContextValue {
  activeCareerId: string | null;
  activeCareer: CareerSummary | null;
  loading: boolean;
  setActiveCareerId: (careerId: string | null) => void;
  refreshActiveCareer: () => Promise<void>;
}

const CareerContext = createContext<CareerContextValue | null>(null);

export function CareerProvider({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  const [activeCareerId, setActiveCareerIdState] = useState<string | null>(null);
  const [activeCareer, setActiveCareer] = useState<CareerSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status !== 'signed-in') {
      setLoading(false);
      return;
    }

    (async () => {
      const stored = await AsyncStorage.getItem(ACTIVE_CAREER_KEY);
      if (stored) setActiveCareerIdState(stored);
      setLoading(false);
    })();
  }, [status]);

  const setActiveCareerId = useCallback((careerId: string | null) => {
    setActiveCareerIdState(careerId);
    if (careerId) {
      AsyncStorage.setItem(ACTIVE_CAREER_KEY, careerId);
    } else {
      AsyncStorage.removeItem(ACTIVE_CAREER_KEY);
    }
  }, []);

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
