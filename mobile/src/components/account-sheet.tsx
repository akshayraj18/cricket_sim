import { useEffect, useState } from 'react';
import { Linking, Modal, Pressable, StyleSheet, Switch, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { isAppleSignInAvailable } from '@/api/socialAuth';
import { Radius, Spacing } from '@/constants/theme';
import { useAuth } from '@/context/AuthContext';
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
  const { user, isGuest, linkApple, linkGoogle, signOut } = useAuth();
  const { replay: replayTutorial } = useOnboardingControls();
  const { permissionGranted, enabled: remindersEnabled, setEnabled: setRemindersEnabled } = useNotifications();

  const handleHowToPlay = () => {
    onClose();
    replayTutorial();
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
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable style={[styles.sheet, { backgroundColor: theme.bgCard }]} onPress={(e) => e.stopPropagation()}>
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

          <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
            Help
          </ThemedText>
          <Pressable
            onPress={handleHowToPlay}
            style={({ pressed }) => [styles.linkButton, { borderColor: theme.border, opacity: pressed ? 0.7 : 1 }]}>
            <ThemedText style={styles.linkButtonText}>How to Play</ThemedText>
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
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    alignItems: 'flex-end',
    justifyContent: 'flex-start',
    padding: Spacing.three,
  },
  sheet: {
    width: 260,
    borderRadius: Radius.lg,
    padding: Spacing.four,
    marginTop: 56,
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
});
