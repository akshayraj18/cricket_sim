import { useCallback, useEffect, useState } from 'react';

import { careersApi } from '@/api/careers';
import { CareerCreateRequest, CareerSummary } from '@/api/types';

interface UseCareersResult {
  careers: CareerSummary[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  createCareer: (body: CareerCreateRequest) => Promise<CareerSummary>;
  deleteCareer: (careerId: string) => Promise<void>;
}

export function useCareers(): UseCareersResult {
  const [careers, setCareers] = useState<CareerSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await careersApi.list();
      setCareers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load careers');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const createCareer = useCallback(async (body: CareerCreateRequest) => {
    const career = await careersApi.create(body);
    setCareers((prev) => [career, ...prev]);
    return career;
  }, []);

  const deleteCareer = useCallback(async (careerId: string) => {
    await careersApi.delete(careerId);
    setCareers((prev) => prev.filter((c) => c.id !== careerId));
  }, []);

  return { careers, loading, error, refresh, createCareer, deleteCareer };
}
