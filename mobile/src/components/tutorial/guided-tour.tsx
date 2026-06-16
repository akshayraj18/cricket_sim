import { useRouter } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, useWindowDimensions, View } from 'react-native';
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
const TAB_BAR_BAND = 92; // approx native tab bar height + breathing room
const HEADER_BAND = 150; // status bar + screen header + segmented-control row

/** A rectangle (screen coords) to leave un-dimmed — the "spotlight". */
interface SpotRect {
  top: number;
  height: number;
}

/**
 * Fully-guided, read-only product tour. The app is frozen behind a tap blocker
 * (the user can only press Back/Next/Skip on the tour card) while the tour
 * drives everything itself: it creates a throwaway demo career (2026 mega
 * draft, autodrafted to a full season) so every screen has real data, then
 * walks tab to tab, dimming the app and spotlighting the relevant region.
 *
 * The demo career is disposable: on Skip OR Finish it's deleted and the user's
 * previously-active career (if any) is restored, then we return to Home. The
 * user's own saves are never touched.
 *
 * Controlled: step index lives in OnboardingProvider and is passed in.
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
  const { createCareer, deleteCareer } = useCareers();
  const { setPayload } = useLeague();

  // Demo career lifecycle. `priorCareerId` is the user's active career before
  // the tour, restored on exit; `demoCareerId` is the throwaway we delete.
  const priorCareerId = useRef<string | null>(null);
  const demoCareerId = useRef<string | null>(null);
  const [preparing, setPreparing] = useState(false);
  const [ready, setReady] = useState(false);

  const index = stepIndex;
  const step: TutorialStep | undefined = TUTORIAL_STEPS[index];

  // On open: build the demo career and OPEN ITS DRAFT (but don't autodraft yet),
  // so the draft step can show the real draft board. The squad/season/stats
  // steps later autodraft the rest (see `fillSquad` in goNext).
  useEffect(() => {
    if (!visible) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setReady(false);
      return;
    }
    let cancelled = false;
    (async () => {
      setPreparing(true);
      onStepChange(0);
      analytics.capture('tutorial_started', { source, kind: 'guided' });
      priorCareerId.current = activeCareerId;
      try {
        const team = 'Mumbai Mavericks';
        const career = await createCareer({
          name: 'Tour Demo',
          user_team_name: team,
          difficulty: 'medium',
          draft_pool_type: 'current', // 2026 rosters + mega draft
        });
        if (cancelled) return;
        demoCareerId.current = career.id;
        setActiveCareerId(career.id);
        // Open the draft so the Mega Draft step shows the live draft board.
        setPayload(await seasonApi.startDraft(career.id));
      } catch {
        // If setup fails the tour still runs as an explainer over empty screens.
      } finally {
        if (!cancelled) {
          setPreparing(false);
          setReady(true);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
    // Run once per open; deps are stable within an open.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  // Finish the draft (autodraft all) so the squad/season/stats screens that
  // follow have a full 25-man roster and an open season. Idempotent.
  const fillSquad = useCallback(async () => {
    const careerId = demoCareerId.current;
    if (!careerId) return;
    try {
      setPayload(await seasonApi.autodraft(careerId, 'all'));
    } catch {
      // Best-effort; the squad step still renders whatever state exists.
    }
  }, [setPayload]);

  // Tear down the demo career and restore the user's prior one, then go Home.
  const finish = useCallback(
    async (reason: 'completed' | 'skipped') => {
      analytics.capture(reason === 'completed' ? 'tutorial_completed' : 'tutorial_skipped', {
        kind: 'guided',
        step: index,
      });
      const demo = demoCareerId.current;
      const prior = priorCareerId.current;
      // Restore the prior active career first so the UI doesn't flash the demo.
      setActiveCareerId(prior);
      demoCareerId.current = null;
      try {
        router.navigate('/(tabs)' as never);
      } catch {
        // ignore navigation hiccups
      }
      onDone();
      if (demo && demo !== prior) {
        try {
          await deleteCareer(demo);
        } catch {
          // Best-effort cleanup; a leftover demo can be deleted from the saves list.
        }
      }
    },
    [analytics, deleteCareer, index, onDone, router, setActiveCareerId]
  );

  const navigateForStep = useCallback(
    (s: TutorialStep) => {
      try {
        if (s.tab) {
          router.navigate(`/(tabs)/${s.tab === 'index' ? '' : s.tab}` as never);
        }
      } catch {
        // Best-effort; the step still explains over the current screen.
      }
    },
    [router]
  );

  // Drive navigation when the visible step changes (after setup completes).
  const lastNavigated = useRef<string | null>(null);
  useEffect(() => {
    if (!visible || !ready || !step) return;
    if (lastNavigated.current === step.key) return;
    lastNavigated.current = step.key;
    navigateForStep(step);
  }, [visible, ready, step, navigateForStep]);

  const isLast = index >= TUTORIAL_STEPS.length - 1;
  const isFirst = index === 0;

  const goNext = useCallback(async () => {
    if (preparing) return;
    if (isLast) {
      finish('completed');
      return;
    }
    const next = TUTORIAL_STEPS[index + 1];
    if (next?.fillSquad) {
      setPreparing(true);
      await fillSquad();
      setPreparing(false);
    }
    onStepChange(Math.min(index + 1, TUTORIAL_STEPS.length - 1));
  }, [fillSquad, finish, index, isLast, onStepChange, preparing]);

  const goBack = useCallback(() => onStepChange(Math.max(0, index - 1)), [index, onStepChange]);

  if (!visible || !step) return null;

  // Compute the spotlight band. Content steps include the header so screen
  // titles + sub-tab buttons are visible inside the highlight.
  const spotlight = step.spotlight ?? 'content';
  const tabTop = screenH - insets.bottom - TAB_BAR_BAND;

  let spot: SpotRect | null;
  let cardSide: 'top' | 'bottom';
  if (spotlight === 'screen') {
    spot = null;
    cardSide = 'bottom';
  } else if (spotlight === 'tabbar') {
    spot = { top: tabTop, height: screenH - tabTop };
    cardSide = 'top';
  } else if (spotlight === 'header') {
    spot = { top: 0, height: insets.top + HEADER_BAND };
    cardSide = 'bottom';
  } else {
    // content: from the very top (so the title + sub-tab row show) down to the
    // tab bar — the full working area of the screen.
    spot = { top: 0, height: tabTop };
    cardSide = 'bottom';
  }

  // While preparing the demo career, show a centered spinner over the dim.
  if (preparing || !ready) {
    return (
      <View style={[StyleSheet.absoluteFill, styles.prep, { backgroundColor: SCRIM }]} pointerEvents="auto">
        <ActivityIndicator color={GOLD} size="large" />
        <ThemedText style={styles.prepText}>Setting up your tour…</ThemedText>
      </View>
    );
  }

  return (
    // pointerEvents="auto" + full-bleed blockers = the app underneath is frozen;
    // only the tour card's buttons are interactive.
    <View style={StyleSheet.absoluteFill} pointerEvents="auto">
      {spot ? (
        <>
          <View style={[styles.dim, { top: 0, height: spot.top }]} />
          <View style={[styles.dim, { top: spot.top + spot.height, bottom: 0 }]} />
          {/* Side rails so taps beside a narrow spotlight are still blocked. */}
          <View
            pointerEvents="none"
            style={[styles.ring, { top: spot.top, height: spot.height, borderColor: GOLD }]}
          />
          {/* Transparent blocker over the spotlight itself so the real buttons
              under the highlight can't be tapped — the tour is read-only. */}
          <Pressable style={[styles.block, { top: spot.top, height: spot.height }]} />
        </>
      ) : (
        <View style={[StyleSheet.absoluteFill, styles.dim]} />
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
            <Pressable onPress={() => finish('skipped')} hitSlop={12}>
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
              disabled={isFirst}
              hitSlop={8}
              style={[styles.backBtn, isFirst && styles.backBtnHidden]}>
              <ThemedText themeColor="textDim" style={styles.backText}>
                Back
              </ThemedText>
            </Pressable>
            <Pressable
              onPress={goNext}
              style={({ pressed }) => [styles.cta, { backgroundColor: theme.green, opacity: pressed ? 0.85 : 1 }]}>
              <ThemedText style={styles.ctaText}>{isLast ? 'Finish' : 'Next'}</ThemedText>
            </Pressable>
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  prep: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.three,
  },
  prepText: {
    fontSize: 15,
    fontWeight: '700',
  },
  dim: {
    position: 'absolute',
    left: 0,
    right: 0,
    backgroundColor: SCRIM,
  },
  block: {
    position: 'absolute',
    left: 0,
    right: 0,
    // Transparent: lets the highlighted UI show but swallows taps.
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
