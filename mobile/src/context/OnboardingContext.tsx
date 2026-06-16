import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';

import { TUTORIAL_STEPS } from '@/components/tutorial/slides';
import { useAuth } from '@/context/AuthContext';
import { TourProvider } from '@/context/TourContext';
import { useOnboarding } from '@/hooks/use-onboarding';

/**
 * Owns the first-run guided tour: decides when it's visible (once after sign-in,
 * or on replay) and holds the current step index. Exposes `replay()` for the
 * account sheet's "How to Play" entry.
 *
 * The actual <GuidedTour> overlay is NOT rendered here — it needs the Career /
 * League contexts (to create a demo career as it walks you through the app),
 * which live BELOW this provider in the tree. Instead this publishes the tour
 * state (via `useTourHost`) and the current step (via <TourProvider>), and a
 * <GuidedTourHost> rendered deeper in the layout reads them and renders the
 * overlay. The step index lives here so it can be published to both.
 */
interface OnboardingContextValue {
  replay: () => void;
}

interface TourHostValue {
  visible: boolean;
  source: 'first_run' | 'replay';
  stepIndex: number;
  setStepIndex: (index: number) => void;
  dismiss: () => void;
}

const OnboardingContext = createContext<OnboardingContextValue | null>(null);
const TourHostContext = createContext<TourHostValue | null>(null);

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  const { visible, source, dismiss, replay } = useOnboarding(status === 'signed-in');
  const [stepIndex, setStepIndex] = useState(0);

  const tourValue = useMemo(
    () => ({
      active: visible,
      currentStep: visible ? (TUTORIAL_STEPS[stepIndex] ?? null) : null,
    }),
    [visible, stepIndex]
  );

  const hostValue = useMemo(
    () => ({ visible, source, stepIndex, setStepIndex, dismiss }),
    [visible, source, stepIndex, dismiss]
  );

  return (
    <OnboardingContext.Provider value={{ replay }}>
      <TourHostContext.Provider value={hostValue}>
        <TourProvider value={tourValue}>{children}</TourProvider>
      </TourHostContext.Provider>
    </OnboardingContext.Provider>
  );
}

export function useOnboardingControls(): OnboardingContextValue {
  const ctx = useContext(OnboardingContext);
  if (!ctx) throw new Error('useOnboardingControls must be used within an OnboardingProvider');
  return ctx;
}

/** Read by <GuidedTourHost>, which renders the overlay deeper in the tree. */
export function useTourHost(): TourHostValue {
  const ctx = useContext(TourHostContext);
  if (!ctx) throw new Error('useTourHost must be used within an OnboardingProvider');
  return ctx;
}
