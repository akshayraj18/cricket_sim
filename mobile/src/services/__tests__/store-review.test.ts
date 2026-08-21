/**
 * The review gate decides whether to spend one of a very small number of
 * prompts iOS will ever show, and a wrong answer is invisible: the OS silently
 * ignores a wasted request, so nothing surfaces either way. That is exactly the
 * kind of rule that has to be tested directly.
 */
import { shouldAskForReview, type ReviewGateState } from '@/services/store-review';

const NOW = new Date('2026-08-20T12:00:00Z');
const VERSION = '1.1.0';
/** Comfortably past the engagement threshold, so other rules are what's under test. */
const SEASONS = 5;

/** Nobody has ever been asked. */
const FRESH: ReviewGateState = { lastAskedAt: null, lastAskedVersion: null, askCount: 0 };

const daysBefore = (n: number) => new Date(NOW.getTime() - n * 24 * 60 * 60 * 1000).toISOString();

describe('shouldAskForReview', () => {
  it('asks a user who has never been asked', () => {
    expect(shouldAskForReview(FRESH, VERSION, NOW, SEASONS)).toBeNull();
  });

  it('does not ask twice on the same build', () => {
    // The common case: someone finishes several seasons in one sitting.
    const state = { lastAskedAt: daysBefore(1), lastAskedVersion: VERSION, askCount: 1 };
    expect(shouldAskForReview(state, VERSION, NOW, SEASONS)).toBe('same-version');
  });

  it('does not ask again inside the cooldown even after an update', () => {
    const state = { lastAskedAt: daysBefore(30), lastAskedVersion: '1.0.0', askCount: 1 };
    expect(shouldAskForReview(state, VERSION, NOW, SEASONS)).toBe('too-soon');
  });

  it('asks again after both a new version and the full cooldown', () => {
    const state = { lastAskedAt: daysBefore(150), lastAskedVersion: '1.0.0', askCount: 1 };
    expect(shouldAskForReview(state, VERSION, NOW, SEASONS)).toBeNull();
  });

  it('stops permanently after three asks', () => {
    const state = { lastAskedAt: daysBefore(900), lastAskedVersion: '0.9.0', askCount: 3 };
    expect(shouldAskForReview(state, VERSION, NOW, SEASONS)).toBe('max-asks');
  });

  it('treats a future-dated timestamp as too soon rather than asking', () => {
    // A clock change must never unlock an extra prompt.
    const state = { lastAskedAt: '2027-01-01T00:00:00Z', lastAskedVersion: '1.0.0', askCount: 1 };
    expect(shouldAskForReview(state, VERSION, NOW, SEASONS)).toBe('too-soon');
  });

  it('treats an unparseable timestamp as too soon rather than asking', () => {
    const state = { lastAskedAt: 'not-a-date', lastAskedVersion: '1.0.0', askCount: 1 };
    expect(shouldAskForReview(state, VERSION, NOW, SEASONS)).toBe('too-soon');
  });

  it('asks a user with a stored count but no timestamp', () => {
    // Storage can be partially cleared; a missing date must not block forever.
    const state = { lastAskedAt: null, lastAskedVersion: '1.0.0', askCount: 1 };
    expect(shouldAskForReview(state, VERSION, NOW, SEASONS)).toBeNull();
  });

  it('does not ask before the second season is finished', () => {
    // The 64% who use the app once must never see this.
    expect(shouldAskForReview(FRESH, VERSION, NOW, 0)).toBe('not-engaged');
    expect(shouldAskForReview(FRESH, VERSION, NOW, 1)).toBe('not-engaged');
  });

  it('asks once the second season is finished', () => {
    expect(shouldAskForReview(FRESH, VERSION, NOW, 2)).toBeNull();
  });

  it('checks the lifetime cap before anything else', () => {
    // A capped user on a brand new version still must not be asked.
    const state = { lastAskedAt: null, lastAskedVersion: null, askCount: 5 };
    expect(shouldAskForReview(state, VERSION, NOW, SEASONS)).toBe('max-asks');
    // Even with no seasons at all, the cap is the reason reported.
    expect(shouldAskForReview(state, VERSION, NOW, 0)).toBe('max-asks');
  });

  it('does not ask on the exact cooldown boundary minus a second', () => {
    const state = { lastAskedAt: daysBefore(120), lastAskedVersion: '1.0.0', askCount: 1 };
    expect(shouldAskForReview(state, VERSION, NOW, SEASONS)).toBeNull();

    const oneSecondShort = new Date(NOW.getTime() - 1000).toISOString();
    const stateShort = { lastAskedAt: oneSecondShort, lastAskedVersion: '1.0.0', askCount: 1 };
    expect(shouldAskForReview(stateShort, VERSION, NOW, SEASONS)).toBe('too-soon');
  });
});
