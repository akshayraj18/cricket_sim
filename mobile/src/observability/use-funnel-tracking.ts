/**
 * Emits the gameplay funnel events by watching the league payload change.
 *
 * Why centrally rather than from the buttons that cause them: a draft can end
 * via "autodraft the rest" or via the last manual pick; a match can finish from
 * the live hub, a quick-sim of the round, or a tournament auto-sim; a season can
 * end from several screens. Capturing at each call site means missing paths, and
 * those gaps are invisible — the event simply never arrives. The payload is the
 * one place every path converges, so transitions in it are the honest signal.
 *
 * Rules this has to respect:
 *  - Fire once per transition, not once per refresh. The payload is refetched on
 *    every tab focus, so equality on the *previous observed* value is what makes
 *    an event an event.
 *  - Never fire on the first observation of a career. Opening the app on a
 *    career that is already in its season is not "the user just finished a
 *    draft" — without this, every cold start would forge a draft_completed.
 *  - Stay silent during the guided tour. The tour drives a throwaway demo career
 *    through draft -> season -> match at speed; counting that as real play would
 *    swamp the funnel with fake completions.
 */
import { useEffect, useRef } from 'react';

import type { LeaguePayload } from '@/api/types';
import { useAnalytics, type AnalyticsEvent } from '@/observability/analytics';

/** The slice of the payload a funnel transition can be derived from. */
export interface FunnelSnapshot {
  careerId: string;
  phase: string;
  draftStarted: boolean;
  matchesPlayed: number;
  liveMatchStatus: string | null;
  completedSeasons: number;
}

export function snapshot(careerId: string, payload: LeaguePayload): FunnelSnapshot {
  return {
    careerId,
    phase: payload.phase,
    draftStarted: Boolean(payload.draft?.started),
    matchesPlayed: payload.match_log?.length ?? 0,
    liveMatchStatus: payload.live_match?.status ?? null,
    completedSeasons: payload.completed_seasons ?? 0,
  };
}

/** Extra properties every funnel event carries, for segmenting in PostHog. */
export interface FunnelContext {
  competition: string;
  match_format: string;
  career_mode: string;
  draft_type: string;
  season: number;
}

export interface FunnelEvent {
  event: AnalyticsEvent;
  props: Record<string, string | number | boolean | null>;
}

/**
 * The events implied by moving from `prev` to `current`.
 *
 * Pure and exported so the transition rules can be tested directly — they are
 * the part that silently produces wrong data if subtly wrong, and a hook that
 * over-fires looks identical to one that works until the funnel is read weeks
 * later. Returns [] when there is no previous snapshot or the career changed,
 * which is what keeps a cold start from forging a completed draft.
 */
export function funnelEventsFor(
  prev: FunnelSnapshot | null,
  current: FunnelSnapshot,
  context: FunnelContext
): FunnelEvent[] {
  if (!prev || prev.careerId !== current.careerId) return [];

  const shared = {
    competition: context.competition,
    match_format: context.match_format,
    career_mode: context.career_mode,
  };
  const events: FunnelEvent[] = [];

  if (!prev.draftStarted && current.draftStarted) {
    events.push({ event: 'draft_started', props: { ...shared, draft_type: context.draft_type } });
  }

  if (prev.phase === 'draft' && current.phase !== 'draft') {
    events.push({ event: 'draft_completed', props: { ...shared, draft_type: context.draft_type } });
  }

  // A quick-simmed round adds several matches at once, so report how many
  // rather than pretending each was a separate user action. `live` means the
  // user's own match finished in the hub.
  const newMatches = current.matchesPlayed - prev.matchesPlayed;
  if (newMatches > 0) {
    const finishedLive =
      prev.liveMatchStatus !== null &&
      prev.liveMatchStatus !== 'complete' &&
      current.liveMatchStatus === 'complete';
    events.push({
      event: 'match_played',
      props: { ...shared, mode: finishedLive ? 'live' : 'quick_sim', matches: newMatches },
    });
  }

  if (prev.phase !== 'playoffs' && current.phase === 'playoffs') {
    events.push({ event: 'playoffs_reached', props: { ...shared, season: context.season } });
  }

  if (current.completedSeasons > prev.completedSeasons) {
    events.push({
      event: 'season_completed',
      props: { ...shared, completed_seasons: current.completedSeasons },
    });
  }

  return events;
}

export function useFunnelTracking(
  careerId: string | null,
  payload: LeaguePayload | null,
  tourActive: boolean
): void {
  const analytics = useAnalytics();
  const previous = useRef<FunnelSnapshot | null>(null);

  useEffect(() => {
    if (tourActive) {
      // Drop the baseline too: when the tour ends the demo career is gone, and
      // a stale snapshot would diff against whatever career loads next.
      previous.current = null;
      return;
    }
    if (!careerId || !payload) {
      previous.current = null;
      return;
    }

    const current = snapshot(careerId, payload);
    const prev = previous.current;
    previous.current = current;

    for (const { event, props } of funnelEventsFor(prev, current, {
      competition: payload.competition,
      match_format: payload.match_format,
      career_mode: payload.career_mode,
      draft_type: payload.draft_type,
      season: payload.season,
    })) {
      analytics.capture(event, props);
    }
  }, [analytics, careerId, payload, tourActive]);
}
