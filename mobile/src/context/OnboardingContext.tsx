import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';

import { GuidedTour } from '@/components/tutorial/guided-tour';
import { TUTORIAL_STEPS } from '@/components/tutorial/slides';
import { useAuth } from '@/context/AuthContext';
import { TourProvider } from '@/context/TourContext';
import { useOnboarding } from '@/hooks/use-onboarding';

/**
 * Owns the first-run guided tour: shows it once after sign-in and exposes
 * `replay()` so the account sheet's "How to Play" entry (rendered deep in the
 * tab tree) can re-open it without prop-drilling.
 *
 * The tour's step index lives here (not inside <GuidedTour>) so it can be
 * published through <TourProvider> to the real screens the tour walks through —
 * e.g. the Squad screen reads the current step to open its Starting XI sub-tab.
 */
interface OnboardingContextValue {
  replay: () => void;
}

const OnboardingContext = createContext<OnboardingContextValue | null>(null);

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

  return (
    <OnboardingContext.Provider value={{ replay }}>
      <TourProvider value={tourValue}>{children}</TourProvider>
      <GuidedTour
        visible={visible}
        source={source}
        stepIndex={stepIndex}
        onStepChange={setStepIndex}
        onDone={dismiss}
      />
    </OnboardingContext.Provider>
  );
}

export function useOnboardingControls(): OnboardingContextValue {
  const ctx = useContext(OnboardingContext);
  if (!ctx) throw new Error('useOnboardingControls must be used within an OnboardingProvider');
  return ctx;
}
