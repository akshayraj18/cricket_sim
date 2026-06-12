import { StyleSheet, View, type ViewStyle } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { getReadableAccentText, pickPillColors, Radius } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { useTheme } from '@/hooks/use-theme';

export function Pill({
  label,
  accentColor,
  secondaryColor,
  selected,
  style,
}: {
  label: string;
  /** When provided, renders the pill in an "accent" style using this color (e.g. team accent). */
  accentColor?: string;
  /** When provided alongside `accentColor`, the pill uses the lighter of the two colors as its background and the darker as its text — a two-tone team look (e.g. RR pink + navy). */
  secondaryColor?: string;
  /** When true, adds a solid border in `accentColor` (or theme green) to mark this pill as the active filter. */
  selected?: boolean;
  style?: ViewStyle;
}) {
  const theme = useTheme();
  const scheme = useColorScheme();

  let backgroundColor = accentColor ? `${accentColor}85` : theme.badgeBg;
  let textColor = accentColor ? getReadableAccentText(accentColor, scheme) : theme.textDim;
  const borderColor = accentColor ?? theme.green;

  if (accentColor && secondaryColor) {
    const picked = pickPillColors(accentColor, secondaryColor);
    backgroundColor = `${picked.background}85`;
    textColor = picked.text;
  }

  return (
    <View
      style={[
        styles.pill,
        { backgroundColor },
        selected && { borderWidth: 1.5, borderColor },
        style,
      ]}>
      <ThemedText style={[styles.text, { color: textColor }]}>{label}</ThemedText>
    </View>
  );
}

const styles = StyleSheet.create({
  pill: {
    borderRadius: Radius.pill,
    paddingHorizontal: 10,
    paddingVertical: 4,
    alignSelf: 'flex-start',
  },
  text: {
    fontSize: 11,
    fontWeight: '700',
  },
});
