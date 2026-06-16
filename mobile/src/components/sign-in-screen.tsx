import * as AppleAuthentication from 'expo-apple-authentication';
import * as WebBrowser from 'expo-web-browser';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Image, Platform, Pressable, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { PRIVACY_POLICY_URL, TERMS_URL } from '@/api/config';
import { isAppleSignInAvailable } from '@/api/socialAuth';
import { Radius, Spacing } from '@/constants/theme';
import { useAuth } from '@/context/AuthContext';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { useTheme } from '@/hooks/use-theme';

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
                Guest play is saved on this device — sign in with Apple or Google to keep your career across devices.
              </ThemedText>

              <ThemedText themeColor="textFaint" style={styles.consent}>
                By continuing you agree to our{' '}
                <ThemedText
                  themeColor="textDim"
                  style={styles.consentLink}
                  onPress={() => WebBrowser.openBrowserAsync(TERMS_URL)}>
                  Terms
                </ThemedText>{' '}
                and{' '}
                <ThemedText
                  themeColor="textDim"
                  style={styles.consentLink}
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
  consent: {
    fontSize: 11,
    lineHeight: 16,
    textAlign: 'center',
    marginTop: Spacing.two,
  },
  consentLink: {
    fontSize: 11,
    textDecorationLine: 'underline',
  },
});
