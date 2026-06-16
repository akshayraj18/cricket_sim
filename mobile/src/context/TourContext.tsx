import { createContext, useContext, type ReactNode } from 'react';

import type { TutorialStep } from '@/components/tutorial/slides';

/**
 * Lets real screens react to the guided tour without prop-drilling. The tour
 * publishes the current step here; screens that the tour walks through (e.g. the
 * Squad screen opening its Starting XI sub-tab) read `currentStep` and adjust
 * their own local state when the tour is on their step. Always safe to call —
 * outside a tour, `active` is false and `currentStep` is null.
 */
export interface TourContextValue {
  active: boolean;
  currentStep: TutorialStep | null;
}

const TourContext = createContext<TourContextValue>({ active: false, currentStep: null });

export function TourProvider({
  value,
  children,
}: {
  value: TourContextValue;
  children: ReactNode;
}) {
  return <TourContext.Provider value={value}>{children}</TourContext.Provider>;
}

export function useTour(): TourContextValue {
  return useContext(TourContext);
}
