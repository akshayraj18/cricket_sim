/**
 * PostHog product analytics. Wraps the app in a PostHogProvider and exposes a
 * tiny typed `useAnalytics()` so screens capture a known set of funnel events
 * rather than ad-hoc strings. No-op (provider renders children only) when no
 * API key is configured.
 */
import { type ReactNode } from 'react';
import { PostHogProvider, usePostHog } from 'posthog-react-native';

import { POSTHOG_API_KEY, POSTHOG_HOST } from '@/api/config';

/** The funnel events we care about — keep this list curated, not free-form. */
export type AnalyticsEvent =
  | 'app_opened'
  | 'signed_in' // props: { method: 'guest' | 'apple' | 'google' }
  | 'account_linked' // props: { provider: 'apple' | 'google' }
  | 'signed_out'
  | 'account_deleted'
  | 'career_created' // props: { team, difficulty, draft_pool }
  | 'draft_completed'
  | 'match_played' // props: { mode: 'quick_sim' | 'live' }
  | 'season_completed'
  | 'impact_sub_used'
  | 'tutorial_started' // props: { source: 'first_run' | 'replay' }
  | 'tutorial_completed' // props: { slides: number }
  | 'tutorial_skipped' // props: { slide: number }
  | 'notifications_enabled' // props: { source: 'prompt' | 'settings' }
  | 'notifications_disabled' // props: { source: 'settings' }
  | 'notification_opened'; // props: { kind: string }

export function AnalyticsProvider({ children }: { children: ReactNode }) {
  if (!POSTHOG_API_KEY) return <>{children}</>;
  return (
    <PostHogProvider
      apiKey={POSTHOG_API_KEY}
      options={{ host: POSTHOG_HOST }}
      autocapture={{ captureScreens: true, captureTouches: false }}>
      {children}
    </PostHogProvider>
  );
}

/** JSON-serialisable property values PostHog accepts. */
type EventProps = Record<string, string | number | boolean | null>;

export interface Analytics {
  capture: (event: AnalyticsEvent, props?: EventProps) => void;
  identify: (distinctId: string, props?: EventProps) => void;
  reset: () => void;
}

/** Typed analytics handle. Safe to call even when PostHog is disabled. */
export function useAnalytics(): Analytics {
  const posthog = usePostHog();
  return {
    capture: (event, props) => posthog?.capture(event, props),
    identify: (distinctId, props) => posthog?.identify(distinctId, props),
    reset: () => posthog?.reset(),
  };
}
