import * as AppleAuthentication from 'expo-apple-authentication';
import * as WebBrowser from 'expo-web-browser';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Image, Pressable, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { PRIVACY_POLICY_URL, TERMS_URL } from '@/api/config';
import { isAppleSignInAvailable } from '@/api/socialAuth';
import { GOLD, Radius, Spacing } from '@/constants/theme';
import { useAuth } from '@/context/AuthContext';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { useTheme } from '@/hooks/use-theme';

// Three quick selling points shown as pills under the hero — each names a core
// fantasy of the game (build, compete, dominate over time) to entice sign-up.
const HIGHLIGHTS: { emoji: string; label: string }[] = [
  { emoji: '⭐', label: 'Mega draft' },
  { emoji: '🏟️', label: 'Live match days' },
  { emoji: '🏆', label: 'Multi-season dynasty' },
];

export function SignInScreen() {
  const theme = useTheme();
  const scheme = useColorScheme();
  const { continueAsGuest, signInWithApple, signInWithGoogle, retry, offline, error, status } = useAuth();
  const isLoading = status === 'loading';

  const [appleAvailable, setAppleAvailable] = useState(false);
  useEffect(() => {
    isAppleSignInAvailable().then(setAppleAvailable);
  }, []);

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.hero}>
          <View style={[styles.markBadge, { backgroundColor: theme.badgeBg, borderColor: theme.border }]}>
            <ThemedText style={styles.mark}>🏏</ThemedText>
          </View>
          <ThemedText themeColor="textFaint" style={styles.eyebrow}>
            YOUR FRANCHISE. YOUR DYNASTY.
          </ThemedText>
          <ThemedText type="title" style={styles.title}>
            Cric
            <ThemedText type="title" style={[styles.title, { color: GOLD }]}>
              Sim
            </ThemedText>
          </ThemedText>
          <ThemedText themeColor="textDim" style={styles.subtitle}>
            Draft a champion squad, outsmart rivals on match day, and build a dynasty across
            season after season. The trophy is yours to win.
          </ThemedText>

          <View style={styles.highlights}>
            {HIGHLIGHTS.map((h) => (
              <View key={h.label} style={[styles.highlightPill, { backgroundColor: theme.badgeBg, borderColor: theme.border }]}>
                <ThemedText style={styles.highlightEmoji}>{h.emoji}</ThemedText>
                <ThemedText themeColor="textDim" style={styles.highlightLabel}>
                  {h.label}
                </ThemedText>
              </View>
            ))}
          </View>
        </View>

        <View style={styles.actions}>
          {error && (
            <ThemedText themeColor="red" style={styles.error}>
              {error}
            </ThemedText>
          )}

          {offline ? (
            // A stored session exists but the backend was unreachable. Offer a
            // retry instead of "Continue as Guest" so the user doesn't start a
            // fresh account and orphan their existing career.
            <>
              <ThemedText themeColor="red" style={styles.error}>
                Couldn&apos;t reach the server. Your saved game is safe — check your connection and try again.
              </ThemedText>
              <Pressable
                onPress={retry}
                disabled={isLoading}
                style={({ pressed }) => [
                  styles.primaryButton,
                  { backgroundColor: theme.green, opacity: pressed ? 0.85 : 1 },
                ]}>
                {isLoading ? (
                  <ActivityIndicator color="#1a1404" />
                ) : (
                  <ThemedText style={styles.primaryButtonText}>Retry</ThemedText>
                )}
              </Pressable>
            </>
          ) : (
            <>
              {appleAvailable && (
                <AppleAuthentication.AppleAuthenticationButton
                  buttonType={AppleAuthentication.AppleAuthenticationButtonType.SIGN_IN}
                  buttonStyle={
                    scheme === 'dark'
                      ? AppleAuthentication.AppleAuthenticationButtonStyle.WHITE
                      : AppleAuthentication.AppleAuthenticationButtonStyle.BLACK
                  }
                  cornerRadius={Radius.sm}
                  style={styles.appleButton}
                  onPress={signInWithApple}
                />
              )}

              <Pressable
                onPress={signInWithGoogle}
                disabled={isLoading}
                style={({ pressed }) => [
                  styles.googleButton,
                  { backgroundColor: theme.bgElevated, borderColor: theme.border, opacity: pressed ? 0.85 : 1 },
                ]}>
                <Image
                  source={{ uri: 'https://developers.google.com/identity/images/g-logo.png' }}
                  style={styles.googleLogo}
                />
                <ThemedText style={styles.googleButtonText}>Sign in with Google</ThemedText>
              </Pressable>

              <View style={styles.dividerRow}>
                <View style={[styles.divider, { backgroundColor: theme.border }]} />
                <ThemedText themeColor="textFaint" style={styles.dividerText}>
                  or
                </ThemedText>
                <View style={[styles.divider, { backgroundColor: theme.border }]} />
              </View>

              <Pressable
                onPress={continueAsGuest}
                disabled={isLoading}
                style={({ pressed }) => [
                  styles.guestButton,
                  { borderColor: theme.border, opacity: pressed ? 0.7 : 1 },
                ]}>
                {isLoading ? (
                  <ActivityIndicator color={theme.text} />
                ) : (
                  <ThemedText themeColor="textDim" style={styles.guestButtonText}>
                    Continue as Guest
                  </ThemedText>
                )}
              </Pressable>

              <ThemedText themeColor="textFaint" style={styles.fineprint}>
                Jump in free as a guest — sign in with Apple or Google to back up your dynasty and play across all your devices.
              </ThemedText>

              <ThemedText themeColor="textFaint" style={styles.fineprint}>
                By continuing, you agree to our{' '}
                <ThemedText
                  themeColor="textDim"
                  style={styles.legalLink}
                  onPress={() => WebBrowser.openBrowserAsync(TERMS_URL)}>
                  Terms of Service
                </ThemedText>{' '}
                and{' '}
                <ThemedText
                  themeColor="textDim"
                  style={styles.legalLink}
                  onPress={() => WebBrowser.openBrowserAsync(PRIVACY_POLICY_URL)}>
                  Privacy Policy
                </ThemedText>
                .
              </ThemedText>
            </>
          )}
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
    gap: Spacing.two,
  },
  markBadge: {
    width: 72,
    height: 72,
    borderRadius: 20,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.one,
  },
  mark: {
    fontSize: 40,
    lineHeight: 48,
  },
  eyebrow: {
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 1.5,
  },
  title: {
    fontSize: 40,
    lineHeight: 46,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
  },
  highlights: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.one,
    marginTop: Spacing.two,
  },
  highlightPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 7,
    paddingHorizontal: 12,
    borderRadius: 999,
    borderWidth: StyleSheet.hairlineWidth,
  },
  highlightEmoji: {
    fontSize: 13,
  },
  highlightLabel: {
    fontSize: 12,
    fontWeight: '700',
  },
  actions: {
    gap: Spacing.two,
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
  appleButton: {
    height: 50,
    width: '100%',
  },
  googleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.two,
    height: 50,
    borderRadius: Radius.sm,
    borderWidth: StyleSheet.hairlineWidth,
  },
  googleLogo: {
    width: 18,
    height: 18,
  },
  googleButtonText: {
    fontWeight: '600',
    fontSize: 15,
  },
  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.two,
    marginVertical: Spacing.one,
  },
  divider: {
    flex: 1,
    height: StyleSheet.hairlineWidth,
  },
  dividerText: {
    fontSize: 12,
    fontWeight: '600',
  },
  guestButton: {
    borderRadius: Radius.sm,
    paddingVertical: 14,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: StyleSheet.hairlineWidth,
  },
  guestButtonText: {
    fontWeight: '600',
    fontSize: 14,
  },
  fineprint: {
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
  },
  legalLink: {
    fontSize: 12,
    lineHeight: 18,
    textDecorationLine: 'underline',
  },
});
