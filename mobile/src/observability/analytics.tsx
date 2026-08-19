/**
 * PostHog product analytics. Wraps the app in a PostHogProvider and exposes a
 * tiny typed `useAnalytics()` so screens capture a known set of funnel events
 * rather than ad-hoc strings. No-op (provider renders children only) when no
 * API key is configured.
 */
import { type ReactNode } from 'react';
import * as Device from 'expo-device';
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
  // --- gameplay funnel. Emitted centrally from payload transitions by
  // useFunnelTracking(), not from individual buttons: a draft can finish via
  // autodraft or the last manual pick, and a match can end from several
  // screens, so per-button capture calls miss paths. See use-funnel-tracking.ts.
  | 'draft_started' // props: { draft_type, competition, match_format }
  | 'draft_completed' // props: { draft_type, competition, match_format }
  | 'match_played' // props: { mode: 'quick_sim' | 'live', competition, match_format }
  | 'playoffs_reached' // props: { competition, match_format, season }
  | 'season_completed' // props: { completed_seasons, competition, match_format }
  | 'impact_sub_used'
  | 'tutorial_started' // props: { source: 'first_run' | 'replay' }
  | 'tutorial_completed' // props: { slides: number }
  | 'tutorial_skipped' // props: { slide: number }
  | 'notifications_enabled' // props: { source: 'prompt' | 'settings' }
  | 'notifications_disabled' // props: { source: 'settings' }
  | 'notification_opened'; // props: { kind: string }

/**
 * Fill in the device fields PostHog can't work out on its own.
 *
 * Out of the box every install reported `$device_type: "Mobile"` with no model
 * at all, so iPhone and iPad were indistinguishable in the data — which made
 * device-specific layout bugs impossible to size. expo-device exposes these
 * synchronously, and its DeviceType separates TABLET from PHONE.
 */
function deviceProperties() {
  const byType: Record<number, string> = {
    [Device.DeviceType.PHONE]: 'Mobile',
    [Device.DeviceType.TABLET]: 'Tablet',
    [Device.DeviceType.DESKTOP]: 'Desktop',
    [Device.DeviceType.TV]: 'TV',
  };
  return {
    $device_name: Device.modelName ?? null,
    $device_model: Device.modelId ?? Device.modelName ?? null,
    $device_manufacturer: Device.manufacturer ?? Device.brand ?? null,
    $device_type: (Device.deviceType != null ? byType[Device.deviceType] : null) ?? 'Mobile',
  };
}

export function AnalyticsProvider({ children }: { children: ReactNode }) {
  if (!POSTHOG_API_KEY) return <>{children}</>;
  return (
    <PostHogProvider
      apiKey={POSTHOG_API_KEY}
      options={{
        host: POSTHOG_HOST,
        // Merge over PostHog's defaults rather than replacing them, so app
        // version/build (which it already gets right) keep flowing through.
        customAppProperties: (defaults) => ({ ...defaults, ...deviceProperties() }),
      }}
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
