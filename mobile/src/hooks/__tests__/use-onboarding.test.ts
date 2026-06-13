import { deriveOnboardingVisibility, type OnboardingState } from '../use-onboarding';

const base: OnboardingState = { ready: true, signedIn: true, seen: false, replaying: false };

describe('deriveOnboardingVisibility', () => {
  it('shows the tutorial on first run (signed in, ready, never seen)', () => {
    expect(deriveOnboardingVisibility(base)).toEqual({ visible: true, source: 'first_run' });
  });

  it('stays hidden until the persisted flag has been read', () => {
    expect(deriveOnboardingVisibility({ ...base, ready: false })).toEqual({
      visible: false,
      source: 'first_run',
    });
  });

  it('does not show before sign-in', () => {
    expect(deriveOnboardingVisibility({ ...base, signedIn: false }).visible).toBe(false);
  });

  it('does not auto-show again once seen', () => {
    expect(deriveOnboardingVisibility({ ...base, seen: true })).toEqual({
      visible: false,
      source: 'replay',
    });
  });

  it('shows again on an explicit replay, with the replay source', () => {
    expect(deriveOnboardingVisibility({ ...base, seen: true, replaying: true })).toEqual({
      visible: true,
      source: 'replay',
    });
  });

  it('reports first_run only the very first time (not seen, not replaying)', () => {
    expect(deriveOnboardingVisibility({ ...base, replaying: true }).source).toBe('replay');
  });
});
