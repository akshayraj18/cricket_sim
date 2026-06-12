import { ActivityIndicator, Pressable, StyleSheet, type ViewStyle } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { getContrastText, Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost';

export function Button({
  label,
  onPress,
  variant = 'secondary',
  disabled,
  loading,
  small,
  style,
  accentColor,
}: {
  label: string;
  onPress: () => void;
  variant?: ButtonVariant;
  disabled?: boolean;
  loading?: boolean;
  small?: boolean;
  style?: ViewStyle;
  /** Team accent color used for the primary variant background. */
  accentColor?: string;
}) {
  const theme = useTheme();
  const isDisabled = disabled || loading;

  const backgroundColor =
    variant === 'primary'
      ? (accentColor ?? theme.green)
      : variant === 'secondary'
        ? theme.bgElevated
        : 'transparent';

  const textColor =
    variant === 'primary'
      ? getContrastText(backgroundColor)
      : variant === 'secondary'
        ? theme.text
        : (accentColor ?? theme.green);

  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      style={({ pressed }) => [
        styles.btn,
        small && styles.btnSmall,
        { backgroundColor, opacity: isDisabled ? 0.5 : pressed ? 0.85 : 1 },
        style,
      ]}>
      {loading ? (
        <ActivityIndicator color={textColor} size="small" />
      ) : (
        <ThemedText style={[styles.label, small && styles.labelSmall, { color: textColor }]} numberOfLines={1}>
          {label}
        </ThemedText>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  btn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: Radius.sm + 2,
    paddingVertical: 13,
    paddingHorizontal: Spacing.three,
  },
  btnSmall: {
    paddingVertical: 9,
    paddingHorizontal: Spacing.two,
    borderRadius: Radius.sm + 1,
  },
  label: {
    fontWeight: '700',
    fontSize: 14,
  },
  labelSmall: {
    fontSize: 12,
  },
});
