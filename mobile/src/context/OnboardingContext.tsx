import { createContext, useContext, type ReactNode } from 'react';

import { GuidedTour } from '@/components/tutorial/guided-tour';
import { useAuth } from '@/context/AuthContext';
import { useOnboarding } from '@/hooks/use-onboarding';

/**
 * Owns the first-run tutorial: shows the guided tour once after sign-in and
 * exposes `replay()` so the account sheet's "How to Play" entry (rendered deep
 * in the tab tree) can re-open it without prop-drilling.
 */
interface OnboardingContextValue {
  replay: () => void;
}

const OnboardingContext = createContext<OnboardingContextValue | null>(null);

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  const { visible, source, dismiss, replay } = useOnboarding(status === 'signed-in');

  return (
    <OnboardingContext.Provider value={{ replay }}>
      {children}
      <GuidedTour visible={visible} source={source} onDone={dismiss} />
    </OnboardingContext.Provider>
  );
}

export function useOnboardingControls(): OnboardingContextValue {
  const ctx = useContext(OnboardingContext);
  if (!ctx) throw new Error('useOnboardingControls must be used within an OnboardingProvider');
  return ctx;
}
