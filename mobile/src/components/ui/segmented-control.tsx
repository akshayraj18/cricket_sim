import { Pressable, ScrollView, StyleSheet } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { getContrastText, Radius, Spacing } from '@/constants/theme';
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
    flexGrow: 1,
    width: '100%',
  },
  seg: {
    flex: 1,
    minWidth: 76,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 9,
    paddingHorizontal: 6,
    borderRadius: Radius.md - 5,
  },
  label: {
    fontSize: 11,
    fontWeight: '700',
  },
});
