import AsyncStorage from '@react-native-async-storage/async-storage';
import { useCallback, useEffect, useState } from 'react';

/**
 * First-run tutorial state. We persist a single `tutorial_seen` flag so the
 * onboarding carousel shows exactly once (after the first sign-in) and never
 * again automatically — but it stays replayable on demand from the account
 * sheet via `replay()`.
 */
const TUTORIAL_SEEN_KEY = 'cricket_sim.tutorial_seen';

/** Inputs that decide whether/why the first-run tutorial should be shown. */
export interface OnboardingState {
  /** True once the persisted `tutorial_seen` flag has been read. */
  ready: boolean;
  /** Whether the user is signed in (tutorial only shows post sign-in). */
  signedIn: boolean;
  /** Whether the tutorial has been seen before (persisted flag). */
  seen: boolean;
  /** Whether the user explicitly re-opened the tutorial. */
  replaying: boolean;
}

/**
 * Pure derivation of the carousel's visibility and analytics source from the
 * onboarding inputs. Extracted so the gating rules can be unit-tested without
 * rendering: show once on first run (signed in, ready, never seen) or whenever
 * the user replays; a replay (or any open after it's been seen) reports the
 * `replay` source, otherwise `first_run`.
 */
export function deriveOnboardingVisibility(s: OnboardingState): {
  visible: boolean;
  source: 'first_run' | 'replay';
} {
  const visible = s.signedIn && s.ready && (!s.seen || s.replaying);
  const source: 'first_run' | 'replay' = s.replaying || s.seen ? 'replay' : 'first_run';
  return { visible, source };
}

export interface Onboarding {
  /** True once we've read the persisted flag (avoids flashing the tutorial). */
  ready: boolean;
  /** Whether the carousel should currently be visible. */
  visible: boolean;
  /** Why the carousel is showing — drives the `tutorial_started` source prop. */
  source: 'first_run' | 'replay';
  /** Mark the tutorial as seen and hide it (completed or skipped). */
  dismiss: () => void;
  /** Re-open the tutorial on demand (e.g. "How to Play" in the account sheet). */
  replay: () => void;
}

export function useOnboarding(signedIn: boolean): Onboarding {
  const [ready, setReady] = useState(false);
  const [seen, setSeen] = useState(true); // assume seen until storage says otherwise
  const [replaying, setReplaying] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const stored = await AsyncStorage.getItem(TUTORIAL_SEEN_KEY);
      if (!cancelled) {
        setSeen(stored === 'true');
        setReady(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const dismiss = useCallback(() => {
    setSeen(true);
    setReplaying(false);
    AsyncStorage.setItem(TUTORIAL_SEEN_KEY, 'true');
  }, []);

  const replay = useCallback(() => {
    setReplaying(true);
  }, []);

  const { visible, source } = deriveOnboardingVisibility({ ready, signedIn, seen, replaying });

  return { ready, visible, source, dismiss, replay };
}
