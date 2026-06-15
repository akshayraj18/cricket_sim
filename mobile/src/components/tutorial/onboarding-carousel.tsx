import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Dimensions,
  FlatList,
  Modal,
  Pressable,
  StyleSheet,
  View,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
} from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { useAnalytics } from '@/observability/analytics';
import { TUTORIAL_SLIDES, type TutorialSlide } from './slides';

/**
 * First-run tutorial as a swipeable modal carousel (Instagram/Duolingo-style).
 * Skippable on every slide; the last slide's button completes it. Visibility
 * and the "seen" flag are owned by `useOnboarding` — this component just
 * renders and reports completion/skip via `onDone`.
 */
export function OnboardingCarousel({
  visible,
  source,
  onDone,
}: {
  visible: boolean;
  /** Where the tutorial was launched from, for analytics. */
  source: 'first_run' | 'replay';
  /** Called when the user finishes or skips — caller persists "seen" + hides. */
  onDone: () => void;
}) {
  const theme = useTheme();
  const analytics = useAnalytics();
  const listRef = useRef<FlatList<TutorialSlide>>(null);
  const [index, setIndex] = useState(0);
  const [width, setWidth] = useState(Dimensions.get('window').width);

  // Fire `tutorial_started` once each time the carousel opens, and reset the
  // page to the first slide so a replay starts from the top.
  useEffect(() => {
    if (visible) {
      setIndex(0);
      analytics.capture('tutorial_started', { source });
    }
    // `source` is derived from `visible`'s cause and stable within an open.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  const isLast = index >= TUTORIAL_SLIDES.length - 1;

  const onScroll = useCallback(
    (e: NativeSyntheticEvent<NativeScrollEvent>) => {
      const next = Math.round(e.nativeEvent.contentOffset.x / width);
      if (next !== index) setIndex(next);
    },
    [index, width]
  );

  const goNext = useCallback(() => {
    if (isLast) {
      analytics.capture('tutorial_completed', { slides: TUTORIAL_SLIDES.length });
      onDone();
      return;
    }
    const next = index + 1;
    listRef.current?.scrollToOffset({ offset: next * width, animated: true });
    setIndex(next);
  }, [analytics, index, isLast, onDone, width]);

  const skip = useCallback(() => {
    analytics.capture('tutorial_skipped', { slide: index });
    onDone();
  }, [analytics, index, onDone]);

  return (
    <Modal visible={visible} animationType="fade" transparent={false} onRequestClose={skip} statusBarTranslucent>
      <View
        style={[styles.container, { backgroundColor: theme.bg }]}
        onLayout={(e) => setWidth(e.nativeEvent.layout.width)}>
        <View style={styles.topBar}>
          <Pressable onPress={skip} hitSlop={12}>
            <ThemedText themeColor="textDim" style={styles.skip}>
              Skip
            </ThemedText>
          </Pressable>
        </View>

        <FlatList
          ref={listRef}
          data={TUTORIAL_SLIDES}
          keyExtractor={(s) => s.key}
          horizontal
          pagingEnabled
          showsHorizontalScrollIndicator={false}
          onScroll={onScroll}
          scrollEventThrottle={16}
          renderItem={({ item }) => (
            <View style={[styles.slide, { width }]}>
              <ThemedText style={styles.emoji}>{item.emoji}</ThemedText>
              <ThemedText style={styles.title}>{item.title}</ThemedText>
              <ThemedText themeColor="textDim" style={styles.body}>
                {item.body}
              </ThemedText>
            </View>
          )}
        />

        <View style={styles.footer}>
          <View style={styles.dots}>
            {TUTORIAL_SLIDES.map((s, i) => (
              <View
                key={s.key}
                style={[
                  styles.dot,
                  { backgroundColor: i === index ? theme.green : theme.border },
                  i === index && styles.dotActive,
                ]}
              />
            ))}
          </View>
          <Pressable
            onPress={goNext}
            style={({ pressed }) => [styles.cta, { backgroundColor: theme.green, opacity: pressed ? 0.85 : 1 }]}>
            <ThemedText style={styles.ctaText}>{isLast ? 'Get Started' : 'Next'}</ThemedText>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    paddingHorizontal: Spacing.four,
    paddingTop: Spacing.six,
    paddingBottom: Spacing.two,
  },
  skip: {
    fontSize: 15,
    fontWeight: '700',
  },
  slide: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: Spacing.five,
    gap: Spacing.three,
  },
  emoji: {
    fontSize: 72,
    lineHeight: 84,
  },
  title: {
    fontSize: 26,
    fontWeight: '800',
    textAlign: 'center',
  },
  body: {
    fontSize: 16,
    lineHeight: 24,
    textAlign: 'center',
  },
  footer: {
    paddingHorizontal: Spacing.four,
    paddingBottom: Spacing.six,
    gap: Spacing.four,
  },
  dots: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: Spacing.one,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: Radius.pill,
  },
  dotActive: {
    width: 20,
  },
  cta: {
    borderRadius: Radius.sm,
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ctaText: {
    fontWeight: '800',
    fontSize: 16,
    color: '#1a1404',
  },
});
