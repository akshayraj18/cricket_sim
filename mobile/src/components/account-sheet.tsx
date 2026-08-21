import { useEffect, useState } from 'react';
import { Alert, Linking, Modal, Pressable, ScrollView, StyleSheet, Switch, View } from 'react-native';

import * as WebBrowser from 'expo-web-browser';

import { PlayerNamesSection } from '@/components/player-names-section';
import { ThemedText } from '@/components/themed-text';
import { PRIVACY_POLICY_URL, RATE_APP_URL, TERMS_URL } from '@/api/config';
import { isAppleSignInAvailable } from '@/api/socialAuth';
import { Radius, Spacing } from '@/constants/theme';
import { useAuth } from '@/context/AuthContext';
import { useError } from '@/context/ErrorContext';
import { useNotifications } from '@/context/NotificationsContext';
import { useOnboardingControls } from '@/context/OnboardingContext';
import { ThemeMode, useAppTheme } from '@/context/ThemeContext';
import { useTheme } from '@/hooks/use-theme';

const MODE_OPTIONS: { key: ThemeMode; label: string; icon: string }[] = [
  { key: 'light', label: 'Light', icon: '☀️' },
  { key: 'dark', label: 'Dark', icon: '🌙' },
  { key: 'system', label: 'System', icon: '⚙️' },
];

export function AccountSheet({ visible, onClose }: { visible: boolean; onClose: () => void }) {
  const theme = useTheme();
  const { mode, setMode } = useAppTheme();
  const { user, isGuest, linkApple, linkGoogle, signOut, deleteAccount } = useAuth();
  const { showError } = useError();
  const { replay: replayTutorial } = useOnboardingControls();
  const { permissionGranted, enabled: remindersEnabled, setEnabled: setRemindersEnabled } = useNotifications();

  const handleHowToPlay = () => {
    onClose();
    replayTutorial();
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      'Delete account?',
      'This permanently deletes your account and all your careers, stats, and match history. This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await deleteAccount();
              onClose();
            } catch (err) {
              showError(err, { onRetry: handleDeleteAccount });
            }
          },
        },
      ]
    );
  };

  // Local const so the null check narrows inside the onPress closure too.
  const rateUrl = RATE_APP_URL;

  /**
   * Open our App Store page. openURL rejects when nothing can handle the link
   * -- most obviously the iOS Simulator, which has no App Store app at all, so
   * this fails there every time and is not a sign the URL is wrong. Say so
   * rather than leaving an unhandled rejection and a bare "invalid link".
   */
  const handleRate = async (url: string) => {
    try {
      await Linking.openURL(url);
    } catch {
      Alert.alert(
        'Could not open the App Store',
        'The App Store is not available on this device. You can rate CricSim by searching for it in the App Store.'
      );
    }
  };

  // Sign in with Apple only exists on iOS 13+ — never offer it elsewhere.
  const [appleAvailable, setAppleAvailable] = useState(false);
  useEffect(() => {
    isAppleSignInAvailable().then(setAppleAvailable);
  }, []);

  const handleSignOut = async () => {
    onClose();
    await signOut();
  };

  return (
    <Modal visible={visible} animationType="fade" transparent onRequestClose={onClose}>
      <View style={styles.root}>
        {/* Full-screen dismiss layer behind the sheet. Kept as a sibling (not a
            parent) of the sheet so it never competes with the ScrollView's pan
            responder — that competition was why scrolling only worked in one
            narrow strip. */}
        <Pressable style={StyleSheet.absoluteFill} onPress={onClose} />
        <View style={[styles.sheet, { backgroundColor: theme.bgCard }]}>
          <ScrollView
            style={styles.scroll}
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator
            keyboardShouldPersistTaps="handled">
          <View style={styles.header}>
            <ThemedText style={styles.name}>{user?.display_name || 'Guest'}</ThemedText>
            <Pressable onPress={onClose} hitSlop={12}>
              <ThemedText themeColor="textDim" style={styles.close}>
                Close
              </ThemedText>
            </Pressable>
          </View>
          {user?.email ? (
            <ThemedText themeColor="textDim" style={styles.email}>
              {user.email}
            </ThemedText>
          ) : null}

          {isGuest ? (
            <>
              <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
                Save your career
              </ThemedText>
              <ThemedText themeColor="textDim" style={styles.helpText}>
                You&apos;re playing as a guest on this device. Link an account to keep your career safe and play
                across devices.
              </ThemedText>
              {appleAvailable && (
                <Pressable
                  onPress={linkApple}
                  style={({ pressed }) => [styles.linkButton, { borderColor: theme.border, opacity: pressed ? 0.7 : 1 }]}>
                  <ThemedText style={styles.linkButtonText}> Link Apple</ThemedText>
                </Pressable>
              )}
              <Pressable
                onPress={linkGoogle}
                style={({ pressed }) => [styles.linkButton, { borderColor: theme.border, opacity: pressed ? 0.7 : 1 }]}>
                <ThemedText style={styles.linkButtonText}>Link Google</ThemedText>
              </Pressable>
            </>
          ) : null}

          <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
            Appearance
          </ThemedText>
          <View style={styles.modeRow}>
            {MODE_OPTIONS.map((opt) => {
              const active = mode === opt.key;
              return (
                <Pressable
                  key={opt.key}
                  onPress={() => setMode(opt.key)}
                  style={[
                    styles.modeOption,
                    { borderColor: theme.border },
                    active && { borderColor: theme.green, backgroundColor: theme.badgeBg },
                  ]}>
                  <ThemedText style={styles.modeIcon}>{opt.icon}</ThemedText>
                  <ThemedText style={[styles.modeLabel, active && { color: theme.green, fontWeight: '800' }]}>
                    {opt.label}
                  </ThemedText>
                </Pressable>
              );
            })}
          </View>

          <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
            Reminders
          </ThemedText>
          {permissionGranted ? (
            <View style={styles.toggleRow}>
              <ThemedText style={styles.toggleLabel}>Season reminders</ThemedText>
              <Switch
                value={remindersEnabled}
                onValueChange={(next) => setRemindersEnabled(next)}
                trackColor={{ true: theme.green }}
              />
            </View>
          ) : (
            <Pressable
              onPress={() => Linking.openSettings()}
              style={({ pressed }) => [styles.linkButton, { borderColor: theme.border, opacity: pressed ? 0.7 : 1 }]}>
              <ThemedText style={styles.linkButtonText}>Enable in Settings</ThemedText>
            </Pressable>
          )}
          <ThemedText themeColor="textDim" style={styles.helpText}>
            {permissionGranted
              ? 'We’ll nudge you when your season or transfer window is waiting.'
              : 'Turn on notifications for cric-sim to get reminded when your season is waiting.'}
          </ThemedText>

          <PlayerNamesSection />

          <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
            Help
          </ThemedText>
          <Pressable
            onPress={handleHowToPlay}
            style={({ pressed }) => [styles.linkButton, { borderColor: theme.border, opacity: pressed ? 0.7 : 1 }]}>
            <ThemedText style={styles.linkButtonText}>How to Play</ThemedText>
          </Pressable>
          {/* Opens our App Store page, rather than the system rating prompt:
              that prompt may only be triggered by a signature moment in play
              (see services/store-review.ts), never by a "rate us" tap.
              Linking, not WebBrowser — this needs to hand off to the App Store
              app. Hidden until EXPO_PUBLIC_APP_STORE_ID is configured. */}
          {rateUrl && (
            <Pressable
              onPress={() => handleRate(rateUrl)}
              style={({ pressed }) => [styles.linkButton, { borderColor: theme.border, opacity: pressed ? 0.7 : 1 }]}>
              <ThemedText style={styles.linkButtonText}>Rate CricSim</ThemedText>
            </Pressable>
          )}

          <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
            Legal
          </ThemedText>
          <Pressable
            onPress={() => WebBrowser.openBrowserAsync(TERMS_URL)}
            style={({ pressed }) => [styles.linkButton, { borderColor: theme.border, opacity: pressed ? 0.7 : 1 }]}>
            <ThemedText style={styles.linkButtonText}>Terms of Service</ThemedText>
          </Pressable>
          <Pressable
            onPress={() => WebBrowser.openBrowserAsync(PRIVACY_POLICY_URL)}
            style={({ pressed }) => [styles.linkButton, { borderColor: theme.border, opacity: pressed ? 0.7 : 1 }]}>
            <ThemedText style={styles.linkButtonText}>Privacy Policy</ThemedText>
          </Pressable>

          <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
            Account
          </ThemedText>
          <Pressable
            onPress={handleSignOut}
            style={({ pressed }) => [
              styles.signOut,
              { borderColor: theme.red, opacity: pressed ? 0.7 : 1 },
            ]}>
            <ThemedText style={[styles.signOutText, { color: theme.red }]}>Sign Out</ThemedText>
          </Pressable>
          <Pressable onPress={handleDeleteAccount} style={styles.deleteAccount} hitSlop={8}>
            <ThemedText style={[styles.deleteAccountText, { color: theme.textDim }]}>Delete Account</ThemedText>
          </Pressable>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    alignItems: 'flex-end',
    justifyContent: 'flex-start',
    padding: Spacing.three,
  },
  sheet: {
    width: 280,
    borderRadius: Radius.lg,
    marginTop: 56,
    overflow: 'hidden',
    // Cap the sheet so a tall menu (guest links + appearance + reminders +
    // help + legal + account) scrolls instead of clipping Sign Out / the
    // legal links off the bottom of the screen.
    maxHeight: '80%',
  },
  scroll: {
    flexGrow: 0,
  },
  scrollContent: {
    padding: Spacing.four,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  name: {
    fontSize: 16,
    fontWeight: '800',
  },
  email: {
    fontSize: 12,
    marginTop: 2,
  },
  close: {
    fontSize: 13,
    fontWeight: '700',
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginTop: Spacing.three,
    marginBottom: Spacing.two,
  },
  helpText: {
    fontSize: 12.5,
    lineHeight: 18,
    marginBottom: Spacing.two,
  },
  linkButton: {
    paddingVertical: 11,
    borderRadius: Radius.sm,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.two,
  },
  linkButtonText: {
    fontSize: 14,
    fontWeight: '700',
  },
  toggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: Spacing.one,
  },
  toggleLabel: {
    fontSize: 14,
    fontWeight: '600',
  },
  modeRow: {
    flexDirection: 'row',
    gap: Spacing.two,
  },
  modeOption: {
    flex: 1,
    alignItems: 'center',
    gap: 4,
    paddingVertical: Spacing.two,
    borderRadius: Radius.sm,
    borderWidth: 1.5,
  },
  modeIcon: {
    fontSize: 18,
  },
  modeLabel: {
    fontSize: 11,
    fontWeight: '700',
  },
  signOut: {
    marginTop: Spacing.two,
    paddingVertical: 12,
    borderRadius: Radius.sm,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  signOutText: {
    fontSize: 14,
    fontWeight: '700',
  },
  deleteAccount: {
    marginTop: Spacing.three,
    alignItems: 'center',
    paddingVertical: Spacing.one,
  },
  deleteAccountText: {
    fontSize: 12.5,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
});
