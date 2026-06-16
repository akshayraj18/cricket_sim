import { useRouter } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, useWindowDimensions, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { seasonApi } from '@/api/season';
import { ThemedText } from '@/components/themed-text';
import { GOLD, Radius, Spacing } from '@/constants/theme';
import { useCareer } from '@/context/CareerContext';
import { useLeague } from '@/context/LeagueContext';
import { useCareers } from '@/hooks/use-careers';
import { useTheme } from '@/hooks/use-theme';
import { useAnalytics } from '@/observability/analytics';
import { TUTORIAL_STEPS, type TutorialStep } from './slides';

const SCRIM = 'rgba(4,8,16,0.74)';
const TAB_BAR_BAND = 92; // approx native tab bar height + a little breathing room
const HEADER_BAND = 104; // approx status bar + screen header

/** A rectangle (in screen coords) to leave un-dimmed — the "spotlight". */
interface SpotRect {
  top: number;
  height: number;
}

/**
 * Guided product tour with a moving spotlight. The real app stays live behind a
 * dim scrim; for each step a REGION of the screen (the tab bar, the header, or
 * the main content panel) is cut out of the dim so it shows through brightly,
 * and an instruction card is placed in the opposite half of the screen.
 *
 * The tour drives the app: it navigates to each screen, and — so the draft,
 * squad, and Starting XI screens have real data to walk through — it creates a
 * career (2026 mega draft) when it reaches the draft step, if the user doesn't
 * already have one. Region-based spotlighting keeps it robust on any state.
 *
 * Controlled: the step index lives in OnboardingProvider (and is published to
 * the real screens via TourContext), passed in as `stepIndex`/`onStepChange`.
 */
export function GuidedTour({
  visible,
  source,
  stepIndex,
  onStepChange,
  onDone,
}: {
  visible: boolean;
  source: 'first_run' | 'replay';
  stepIndex: number;
  onStepChange: (index: number) => void;
  onDone: () => void;
}) {
  const theme = useTheme();
  const router = useRouter();
  const analytics = useAnalytics();
  const insets = useSafeAreaInsets();
  const { height: screenH } = useWindowDimensions();
  const { activeCareerId, setActiveCareerId } = useCareer();
  const { createCareer } = useCareers();
  const { payload, setPayload, refresh } = useLeague();
  const [busy, setBusy] = useState(false);

  const index = stepIndex;
  const step: TutorialStep | undefined = TUTORIAL_STEPS[index];

  const navigateForStep = useCallback(
    (s: TutorialStep) => {
      try {
        if (s.route) {
          router.navigate(s.route as never);
        } else if (s.tab) {
          // Dismiss the New Career modal (or any pushed screen) before switching
          // tabs, so a tab step never shows underneath a leftover modal.
          if (router.canDismiss?.()) router.dismissAll();
          router.navigate(`/(tabs)/${s.tab === 'index' ? '' : s.tab}` as never);
        }
      } catch {
        // Best-effort: if a target isn't reachable yet, the step's explanation
        // still shows over the current screen.
      }
    },
    [router]
  );

  // Reset to the first step + fire analytics once per open.
  useEffect(() => {
    if (visible) {
      onStepChange(0);
      analytics.capture('tutorial_started', { source, kind: 'guided' });
    }
    // `source`/`onStepChange` are stable within an open.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  // Drive navigation whenever the visible step changes.
  const lastNavigated = useRef<string | null>(null);
  useEffect(() => {
    if (!visible || !step) return;
    if (lastNavigated.current === step.key) return;
    lastNavigated.current = step.key;
    navigateForStep(step);
  }, [visible, step, navigateForStep]);

  const isLast = index >= TUTORIAL_STEPS.length - 1;
  const isFirst = index === 0;

  // Create a demo career (2026 mega draft) and open its draft so the draft
  // board shows real franchises + the player pool. No-op if a career exists.
  const ensureCareer = useCallback(async () => {
    let careerId = activeCareerId;
    if (!careerId) {
      const team = 'Mumbai Mavericks';
      const career = await createCareer({
        name: `${team} Career`,
        user_team_name: team,
        difficulty: 'medium',
        draft_pool_type: 'current', // 2026 rosters + mega draft
      });
      careerId = career.id;
      setActiveCareerId(career.id);
    }
    try {
      if (careerId) setPayload(await seasonApi.startDraft(careerId));
    } catch {
      // Draft may already be started/finished — fine, the board still renders.
    }
  }, [activeCareerId, createCareer, setActiveCareerId, setPayload]);

  // Finish the draft so the Squad / Starting XI / Season screens that follow
  // have a full 25-man roster and an open season. No-op once past the draft.
  const inDraft = payload?.phase === 'draft';
  const fillSquad = useCallback(async () => {
    const careerId = activeCareerId;
    if (!careerId) return;
    try {
      if (inDraft) {
        setPayload(await seasonApi.autodraft(careerId, 'all'));
      } else {
        await refresh();
      }
    } catch {
      // Best-effort; the squad step still renders whatever state exists.
    }
  }, [activeCareerId, inDraft, refresh, setPayload]);

  const goNext = useCallback(async () => {
    if (busy) return;
    if (isLast) {
      analytics.capture('tutorial_completed', { steps: TUTORIAL_STEPS.length, kind: 'guided' });
      onDone();
      return;
    }
    const next = TUTORIAL_STEPS[index + 1];
    if (next?.ensureCareer || next?.fillSquad) {
      setBusy(true);
      if (next.ensureCareer) await ensureCareer();
      if (next.fillSquad) await fillSquad();
      setBusy(false);
    }
    onStepChange(Math.min(index + 1, TUTORIAL_STEPS.length - 1));
  }, [analytics, busy, ensureCareer, fillSquad, index, isLast, onDone, onStepChange]);

  const goBack = useCallback(() => onStepChange(Math.max(0, index - 1)), [index, onStepChange]);

  const skip = useCallback(() => {
    analytics.capture('tutorial_skipped', { step: index, kind: 'guided' });
    onDone();
  }, [analytics, index, onDone]);

  if (!visible || !step) return null;

  // Compute the spotlight rectangle (a horizontal band) for this step.
  const spotlight = step.spotlight ?? 'content';
  const tabTop = screenH - insets.bottom - TAB_BAR_BAND;

  let spot: SpotRect | null;
  let cardSide: 'top' | 'bottom';
  if (spotlight === 'screen') {
    spot = null;
    cardSide = 'bottom';
  } else if (spotlight === 'tabbar') {
    // The whole tab bar, full height to the bottom edge.
    spot = { top: tabTop, height: screenH - tabTop };
    cardSide = 'top';
  } else if (spotlight === 'header') {
    spot = { top: insets.top, height: HEADER_BAND };
    cardSide = 'bottom';
  } else {
    // content: the ENTIRE main panel band between the header and the tab bar,
    // so the highlighted area covers the full working area the step describes.
    const top = insets.top + HEADER_BAND;
    spot = { top, height: Math.max(160, tabTop - top) };
    cardSide = 'bottom';
  }

  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="box-none">
      {spot ? (
        <>
          {/* Dim panels above and below the spotlight band. */}
          <Pressable style={[styles.dim, { top: 0, height: spot.top }]} onPress={goNext} />
          <Pressable style={[styles.dim, { top: spot.top + spot.height, bottom: 0 }]} onPress={goNext} />
          {/* Bright ring around the spotlight so it reads as "look here". */}
          <View
            pointerEvents="none"
            style={[styles.ring, { top: spot.top, height: spot.height, borderColor: GOLD }]}
          />
        </>
      ) : (
        <Pressable style={[StyleSheet.absoluteFill, styles.dim]} onPress={goNext} />
      )}

      <View
        pointerEvents="box-none"
        style={[
          styles.cardWrap,
          cardSide === 'top'
            ? { top: insets.top + Spacing.two }
            : { bottom: insets.bottom + Spacing.two },
        ]}>
        <View style={[styles.card, { backgroundColor: theme.bgCard, borderColor: theme.border }]}>
          <View style={styles.cardHeader}>
            <ThemedText style={styles.emoji}>{step.emoji}</ThemedText>
            <ThemedText themeColor="textFaint" style={styles.counter}>
              {index + 1} / {TUTORIAL_STEPS.length}
            </ThemedText>
            <Pressable onPress={skip} hitSlop={12}>
              <ThemedText themeColor="textDim" style={styles.skip}>
                Skip
              </ThemedText>
            </Pressable>
          </View>

          <ThemedText style={styles.title}>{step.title}</ThemedText>
          <ThemedText themeColor="textDim" style={styles.body}>
            {step.body}
          </ThemedText>

          <View style={styles.dots}>
            {TUTORIAL_STEPS.map((s, i) => (
              <View
                key={s.key}
                style={[
                  styles.dot,
                  { backgroundColor: i === index ? GOLD : theme.border },
                  i === index && styles.dotActive,
                ]}
              />
            ))}
          </View>

          <View style={styles.actions}>
            <Pressable
              onPress={goBack}
              disabled={isFirst || busy}
              hitSlop={8}
              style={[styles.backBtn, isFirst && styles.backBtnHidden]}>
              <ThemedText themeColor="textDim" style={styles.backText}>
                Back
              </ThemedText>
            </Pressable>
            <Pressable
              onPress={goNext}
              disabled={busy}
              style={({ pressed }) => [
                styles.cta,
                { backgroundColor: theme.green, opacity: pressed || busy ? 0.85 : 1 },
              ]}>
              <ThemedText style={styles.ctaText}>
                {busy ? 'Setting up…' : isLast ? 'Finish' : 'Next'}
              </ThemedText>
            </Pressable>
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  dim: {
    position: 'absolute',
    left: 0,
    right: 0,
    backgroundColor: SCRIM,
  },
  ring: {
    position: 'absolute',
    left: Spacing.one,
    right: Spacing.one,
    borderWidth: 2,
    borderRadius: Radius.lg,
  },
  cardWrap: {
    position: 'absolute',
    left: 0,
    right: 0,
    paddingHorizontal: Spacing.four,
  },
  card: {
    borderRadius: Radius.lg,
    borderWidth: StyleSheet.hairlineWidth,
    padding: Spacing.four,
    gap: Spacing.two,
    shadowColor: '#000',
    shadowOpacity: 0.4,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 8 },
    elevation: 12,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.two,
  },
  emoji: {
    fontSize: 28,
    lineHeight: 34,
  },
  counter: {
    flex: 1,
    fontSize: 13,
    fontWeight: '700',
  },
  skip: {
    fontSize: 14,
    fontWeight: '700',
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
  },
  body: {
    fontSize: 15,
    lineHeight: 22,
  },
  dots: {
    flexDirection: 'row',
    gap: 6,
    marginTop: Spacing.one,
  },
  dot: {
    width: 7,
    height: 7,
    borderRadius: Radius.pill,
  },
  dotActive: {
    width: 18,
  },
  actions: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: Spacing.one,
  },
  backBtn: {
    paddingVertical: 10,
    paddingHorizontal: 4,
  },
  backBtnHidden: {
    opacity: 0,
  },
  backText: {
    fontSize: 15,
    fontWeight: '700',
  },
  cta: {
    borderRadius: Radius.sm,
    paddingVertical: 14,
    paddingHorizontal: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ctaText: {
    fontWeight: '800',
    fontSize: 15,
    color: '#1a1404',
  },
});
