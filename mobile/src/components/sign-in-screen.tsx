import { ActivityIndicator, Pressable, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { Radius, Spacing } from '@/constants/theme';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/hooks/use-theme';

export function SignInScreen() {
  const theme = useTheme();
  const { continueAsGuest, error, status } = useAuth();
  const isLoading = status === 'loading';

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.hero}>
          <ThemedText style={styles.mark}>🏏</ThemedText>
          <ThemedText type="title" style={styles.title}>
            IPL Franchise{'\n'}Universe
          </ThemedText>
          <ThemedText themeColor="textDim" style={styles.subtitle}>
            Build a 21-player squad, run toss-to-trophy match days, and create a multi-season
            league history.
          </ThemedText>
        </View>

        <View style={styles.actions}>
          {error && (
            <ThemedText themeColor="red" style={styles.error}>
              {error}
            </ThemedText>
          )}

          <Pressable
            onPress={continueAsGuest}
            disabled={isLoading}
            style={({ pressed }) => [
              styles.primaryButton,
              { backgroundColor: theme.green, opacity: pressed ? 0.85 : 1 },
            ]}>
            {isLoading ? (
              <ActivityIndicator color="#1a1404" />
            ) : (
              <ThemedText style={styles.primaryButtonText}>Continue as Guest</ThemedText>
            )}
          </Pressable>

          <ThemedText themeColor="textFaint" style={styles.fineprint}>
            Sign in with Apple or Google coming soon — start as a guest and link an account later.
          </ThemedText>
        </View>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.four,
    paddingBottom: Spacing.four,
  },
  hero: {
    flex: 1,
    justifyContent: 'center',
    gap: Spacing.three,
  },
  mark: {
    fontSize: 48,
    lineHeight: 56,
  },
  title: {
    fontSize: 36,
    lineHeight: 42,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
  },
  actions: {
    gap: Spacing.three,
  },
  error: {
    textAlign: 'center',
  },
  primaryButton: {
    borderRadius: Radius.sm,
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryButtonText: {
    fontWeight: '700',
    fontSize: 15,
    color: '#1a1404',
  },
  fineprint: {
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
  },
});
