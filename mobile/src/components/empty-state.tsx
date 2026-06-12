import { router } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

export function EmptyState({
  title,
  message,
  actionLabel,
  onAction,
}: {
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  const theme = useTheme();

  return (
    <View style={styles.container}>
      <ThemedText style={styles.title}>{title}</ThemedText>
      <ThemedText themeColor="textDim" style={styles.message}>
        {message}
      </ThemedText>
      {actionLabel && onAction && (
        <Pressable
          onPress={onAction}
          style={({ pressed }) => [
            styles.button,
            { backgroundColor: theme.green, opacity: pressed ? 0.85 : 1 },
          ]}>
          <ThemedText style={styles.buttonText}>{actionLabel}</ThemedText>
        </Pressable>
      )}
    </View>
  );
}

/** Convenience wrapper for "select a career on Home" prompts shown on the other tabs. */
export function NoActiveCareer() {
  return (
    <EmptyState
      title="No Career Selected"
      message="Choose or start a career from the Home tab to continue."
      actionLabel="Go to Home"
      onAction={() => router.push('/(tabs)')}
    />
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.two,
    paddingHorizontal: Spacing.five,
  },
  title: {
    fontWeight: '700',
    fontSize: 17,
    textAlign: 'center',
  },
  message: {
    fontSize: 13,
    lineHeight: 19,
    textAlign: 'center',
  },
  button: {
    marginTop: Spacing.two,
    borderRadius: Radius.sm,
    paddingVertical: 12,
    paddingHorizontal: Spacing.four,
  },
  buttonText: {
    fontWeight: '700',
    fontSize: 13,
    color: '#1a1404',
  },
});
