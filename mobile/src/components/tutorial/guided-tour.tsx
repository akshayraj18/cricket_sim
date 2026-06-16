import { useRouter } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, useWindowDimensions, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { GOLD, Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { useAnalytics } from '@/observability/analytics';
import { TUTORIAL_STEPS, type TutorialStep } from './slides';

const SCRIM = 'rgba(4,8,16,0.74)';
const TAB_BAR_BAND = 92; // approx native tab bar height + a little breathing room

/** A rectangle (in screen coords) to leave un-dimmed — the "spotlight". */
interface SpotRect {
  top: number;
  height: number;
}

/**
 * Guided product tour with a moving spotlight. The real app stays live behind a
 * dim scrim; for each step a REGION of the screen (the tab bar, the header, or
 * the main content panel) is cut out of the dim so it shows through brightly,
 * and an instruction card is placed in the opposite half of the screen. As you
 * advance, the spotlight moves to the area the next step describes.
 *
 * Region-based (rather than exact-element) spotlighting means it works on any
 * account state — including a brand-new account whose squad/season screens have
 * no data yet — without threading refs into every screen.
 *
 * Visibility + the "seen" flag are owned by `useOnboarding`; this reports
 * completion/skip via `onDone`.
 */
export function GuidedTour({
  visible,
  source,
  onDone,
}: {
  visible: boolean;
  source: 'first_run' | 'replay';
  onDone: () => void;
}) {
  const theme = useTheme();
  const router = useRouter();
  const analytics = useAnalytics();
  const insets = useSafeAreaInsets();
  const { height: screenH } = useWindowDimensions();
  const [index, setIndex] = useState(0);

  const step: TutorialStep | undefined = TUTORIAL_STEPS[index];

  const navigateForStep = useCallback(
    (s: TutorialStep) => {
      try {
        if (s.route) {
          router.navigate(s.route as never);
        } else if (s.tab) {
          router.navigate(`/(tabs)/${s.tab === 'index' ? '' : s.tab}` as never);
        }
      } catch {
        // Best-effort: if a target isn't reachable yet, the step's explanation
        // still shows over the current screen.
      }
    },
    [router]
  );

  useEffect(() => {
    if (visible) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setIndex(0);
      analytics.capture('tutorial_started', { source, kind: 'guided' });
    }
    // `source` is stable within an open.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  const lastNavigated = useRef<string | null>(null);
  useEffect(() => {
    if (!visible || !step) return;
    if (lastNavigated.current === step.key) return;
    lastNavigated.current = step.key;
    navigateForStep(step);
  }, [visible, step, navigateForStep]);

  const isLast = index >= TUTORIAL_STEPS.length - 1;
  const isFirst = index === 0;

  const goNext = useCallback(() => {
    if (isLast) {
      analytics.capture('tutorial_completed', { steps: TUTORIAL_STEPS.length, kind: 'guided' });
      onDone();
      return;
    }
    setIndex((i) => Math.min(i + 1, TUTORIAL_STEPS.length - 1));
  }, [analytics, isLast, onDone]);

  const goBack = useCallback(() => setIndex((i) => Math.max(0, i - 1)), []);

  const skip = useCallback(() => {
    analytics.capture('tutorial_skipped', { step: index, kind: 'guided' });
    onDone();
  }, [analytics, index, onDone]);

  if (!visible || !step) return null;

  // Compute the spotlight rectangle (a horizontal band) for this step, and
  // decide whether the instruction card sits above or below it.
  const spotlight = step.spotlight ?? 'content';
  const headerTop = insets.top;
  const tabTop = screenH - insets.bottom - TAB_BAR_BAND;

  let spot: SpotRect | null;
  let cardSide: 'top' | 'bottom';
  if (spotlight === 'screen') {
    spot = null; // dim the whole screen, card centred
    cardSide = 'bottom';
  } else if (spotlight === 'tabbar') {
    spot = { top: tabTop, height: screenH - tabTop };
    cardSide = 'top'; // card above the tab bar
  } else if (spotlight === 'header') {
    spot = { top: headerTop, height: 96 };
    cardSide = 'bottom'; // card below the header
  } else {
    // content: spotlight the upper portion of the main panel band, and drop the
    // card into the gap below it (between the spotlight and the tab bar) so the
    // two never overlap.
    const top = headerTop + 96;
    const height = Math.max(160, (tabTop - top) * 0.55);
    spot = { top, height };
    cardSide = 'bottom';
  }

  return (
    // Absolute-fill overlay above the whole app. box-none lets the dimmed app
    // show through; the dim segments + card capture touches.
    <View style={StyleSheet.absoluteFill} pointerEvents="box-none">
      {spot ? (
        // Four dim panels surrounding the transparent spotlight band. Tapping
        // any dim area advances, like a coach-mark.
        <>
          <Pressable style={[styles.dim, { top: 0, height: spot.top }]} onPress={goNext} />
          <Pressable
            style={[styles.dim, { top: spot.top + spot.height, bottom: 0 }]}
            onPress={goNext}
          />
          {/* A bright ring around the spotlight to make it pop. */}
          <View
            pointerEvents="none"
            style={[
              styles.ring,
              { top: spot.top, height: spot.height, borderColor: GOLD },
            ]}
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
            ? { top: insets.top + Spacing.two, bottom: undefined }
            : { bottom: insets.bottom + Spacing.two, top: undefined },
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
