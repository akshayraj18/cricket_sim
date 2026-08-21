/**
 * Asking for an App Store rating, within Apple's rules.
 *
 * The rules are unusually strict here, so they are worth stating:
 *
 *  - **No pre-prompt.** App Store Review Guideline 1.1.7 requires the system
 *    API and disallows custom review prompts, so the familiar "Enjoying the
 *    app? [Yes] [No]" gate is not an option — nor is any custom dialog that
 *    imitates the system one. We call the system prompt directly.
 *  - **Not from a button.** Expo's own guidance is to call this "after the user
 *    has finished some signature interaction", never from a tap that means
 *    "rate now". The Settings row is a plain link to our App Store page, which
 *    is a different thing and is allowed.
 *  - **iOS decides.** `requestReview()` resolves whether or not anything was
 *    shown; the system allows roughly three prompts per year and silently
 *    ignores the rest. So we cannot know if the user saw it, which is exactly
 *    why the local guards below matter: a wasted request is invisible.
 *
 * The moment we choose is finishing a season — the clearest "that went well"
 * beat the game has. Match wins are far too frequent to qualify.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Application from 'expo-application';

/** When we last asked, as an ISO date. */
const LAST_ASKED_KEY = 'cricket_sim.review_last_asked_at';
/** The app version we last asked on, so an update is required before re-asking. */
const LAST_VERSION_KEY = 'cricket_sim.review_last_asked_version';
/** How many times we have ever asked. */
const ASK_COUNT_KEY = 'cricket_sim.review_ask_count';

/**
 * Minimum gap between requests. Comfortably longer than a season takes, so a
 * player who finishes several in a row is asked once, not once each.
 */
const MIN_DAYS_BETWEEN_ASKS = 120;

/**
 * Lifetime cap. iOS ignores anything past ~3 a year regardless, and a person
 * who has declined three times has answered the question.
 */
const MAX_ASKS = 3;

/**
 * Seasons a player must have finished before we ask at all.
 *
 * Two, not one, per the plan in `docs/ideas.txt`: iOS grants only about three
 * prompts a year, so they should go to people who have kept playing rather
 * than to everyone who reaches a first season end. One constant to change if
 * that proves too strict — the funnel data will say.
 */
const MIN_COMPLETED_SEASONS = 2;

const DAY_MS = 24 * 60 * 60 * 1000;

/**
 * expo-store-review is a native module: it exists only in a binary built after
 * it was added. A static import throws while the module graph loads — before
 * any component can catch it — taking down whatever screen imported it. Failing
 * to ask for a review must never be visible to anyone, so it is loaded lazily
 * and every failure is swallowed.
 */
function loadStoreReview(): typeof import('expo-store-review') | null {
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    return require('expo-store-review') as typeof import('expo-store-review');
  } catch {
    return null;
  }
}

/** Why a request was or wasn't made. Returned for tests and analytics, not for the user. */
export type ReviewOutcome =
  | 'requested'
  | 'unavailable' // no native module, or the OS says it cannot review (e.g. TestFlight)
  | 'too-soon' // inside the cooldown
  | 'same-version' // already asked on this build
  | 'not-engaged' // hasn't finished enough seasons yet
  | 'max-asks'; // asked enough times

export interface ReviewGateState {
  lastAskedAt: string | null;
  lastAskedVersion: string | null;
  askCount: number;
}

/**
 * The decision, split out from the side effects so the rules can be tested
 * without a native module, a clock, or storage.
 */
export function shouldAskForReview(
  state: ReviewGateState,
  currentVersion: string,
  now: Date,
  completedSeasons: number
): Exclude<ReviewOutcome, 'requested' | 'unavailable'> | null {
  if (state.askCount >= MAX_ASKS) return 'max-asks';
  if (completedSeasons < MIN_COMPLETED_SEASONS) return 'not-engaged';
  // Requiring a new version means an unchanged build can never re-ask, however
  // many seasons are completed.
  if (state.lastAskedVersion && state.lastAskedVersion === currentVersion) return 'same-version';
  if (state.lastAskedAt) {
    const elapsed = now.getTime() - new Date(state.lastAskedAt).getTime();
    // A corrupt or future-dated timestamp reads as "not enough time has
    // passed", which errs toward not pestering anyone.
    if (!(elapsed >= MIN_DAYS_BETWEEN_ASKS * DAY_MS)) return 'too-soon';
  }
  return null;
}

async function readState(): Promise<ReviewGateState> {
  const [lastAskedAt, lastAskedVersion, count] = await Promise.all([
    AsyncStorage.getItem(LAST_ASKED_KEY),
    AsyncStorage.getItem(LAST_VERSION_KEY),
    AsyncStorage.getItem(ASK_COUNT_KEY),
  ]);
  const parsed = Number(count);
  return {
    lastAskedAt,
    lastAskedVersion,
    askCount: Number.isFinite(parsed) && parsed > 0 ? parsed : 0,
  };
}

/**
 * Ask for a review if every guard allows it. Never throws and never surfaces
 * anything to the user: the worst case is that no prompt appears.
 */
export async function maybeRequestReview(
  completedSeasons: number,
  now: Date = new Date()
): Promise<ReviewOutcome> {
  try {
    const StoreReview = loadStoreReview();
    if (!StoreReview) return 'unavailable';

    const state = await readState();
    const version = Application.nativeApplicationVersion ?? 'unknown';
    const blocked = shouldAskForReview(state, version, now, completedSeasons);
    if (blocked) return blocked;

    // Ask the OS last: `isAvailableAsync` is false on TestFlight and
    // `hasAction` false where no review flow exists, and neither should burn a
    // slot or move the cooldown.
    if (!(await StoreReview.isAvailableAsync())) return 'unavailable';
    if (!(await StoreReview.hasAction())) return 'unavailable';

    // Record before requesting. If the write failed afterwards we could ask
    // again on the next season, which is the failure worth avoiding.
    await Promise.all([
      AsyncStorage.setItem(LAST_ASKED_KEY, now.toISOString()),
      AsyncStorage.setItem(LAST_VERSION_KEY, version),
      AsyncStorage.setItem(ASK_COUNT_KEY, String(state.askCount + 1)),
    ]);

    await StoreReview.requestReview();
    return 'requested';
  } catch {
    // Includes the case where the OS shows nothing at all — indistinguishable
    // from success by design.
    return 'unavailable';
  }
}
