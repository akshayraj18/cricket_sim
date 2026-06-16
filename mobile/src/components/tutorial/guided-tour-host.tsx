import { GuidedTour } from '@/components/tutorial/guided-tour';
import { useTourHost } from '@/context/OnboardingContext';

/**
 * Renders the guided tour overlay. Mounted DEEP in the provider tree (inside
 * the Career + League providers) so the tour can read/create career data — the
 * onboarding visibility + step state it needs is published up in
 * OnboardingProvider and read here via `useTourHost`.
 */
export function GuidedTourHost() {
  const { visible, source, stepIndex, setStepIndex, dismiss } = useTourHost();
  return (
    <GuidedTour
      visible={visible}
      source={source}
      stepIndex={stepIndex}
      onStepChange={setStepIndex}
      onDone={dismiss}
    />
  );
}
