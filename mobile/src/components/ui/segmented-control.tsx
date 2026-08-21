import { Pressable, ScrollView, StyleSheet } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { getContrastText, Radius } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

export function SegmentedControl<T extends string>({
  segments,
  value,
  onChange,
  accentColor,
}: {
  segments: { key: T; label: string }[];
  value: T;
  onChange: (key: T) => void;
  /** Active segment background, defaults to the team primary color via theme.green fallback. */
  accentColor?: string;
}) {
  const theme = useTheme();
  const activeBg = accentColor ?? theme.green;
  const activeTextColor = getContrastText(activeBg);

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      style={[styles.container, { backgroundColor: theme.bgElevated }]}
      contentContainerStyle={styles.content}>
      {segments.map((seg) => {
        const active = seg.key === value;
        return (
          <Pressable
            key={seg.key}
            onPress={() => onChange(seg.key)}
            style={[styles.seg, active && { backgroundColor: activeBg }]}>
            {/* One line, at full size: the segment now widens to fit the label
                rather than the label shrinking to fit the segment. */}
            <ThemedText
              style={[styles.label, active && { color: activeTextColor }]}
              themeColor={active ? undefined : 'textDim'}
              numberOfLines={1}>
              {seg.label}
            </ThemedText>
          </Pressable>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: Radius.md - 2,
    padding: 4,
  },
  content: {
    gap: 4,
    // No `width: '100%'`: on a horizontal ScrollView that pins the content to
    // exactly the viewport, so it can never scroll and the segments have to
    // compress instead — which is how "Bowling Plan" became "Bowling Pl…".
    // flexGrow still fills the width whenever the labels do fit.
    flexGrow: 1,
  },
  seg: {
    // Share any leftover width, but never shrink below the label: scrolling a
    // too-wide row is always better than an unreadable truncated one. This is
    // what keeps the labels intact at large accessibility text sizes too.
    flexGrow: 1,
    flexShrink: 0,
    minWidth: 64,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 7,
    paddingHorizontal: 8,
    borderRadius: Radius.md - 5,
  },
  label: {
    fontSize: 11,
    fontWeight: '700',
    textAlign: 'center',
  },
});
