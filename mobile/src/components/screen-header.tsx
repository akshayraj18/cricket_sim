import { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { AccountSheet } from '@/components/account-sheet';
import { ThemedText } from '@/components/themed-text';
import { Radius, Spacing } from '@/constants/theme';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/hooks/use-theme';

function initials(name: string | null): string {
  if (!name) return 'GU';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export function ScreenHeader({ eyebrow, title }: { eyebrow?: string; title: string }) {
  const theme = useTheme();
  const { user } = useAuth();
  const [accountVisible, setAccountVisible] = useState(false);

  return (
    <View style={styles.appbar}>
      <View style={styles.titleBlock}>
        {eyebrow && (
          <ThemedText themeColor="textFaint" style={styles.eyebrow}>
            {eyebrow}
          </ThemedText>
        )}
        <ThemedText style={styles.title}>{title}</ThemedText>
      </View>
      <Pressable
        onPress={() => setAccountVisible(true)}
        style={[styles.avatar, { backgroundColor: theme.bgCard, borderColor: theme.border }]}>
        <ThemedText style={styles.avatarText}>{initials(user?.display_name ?? null)}</ThemedText>
      </Pressable>
      <AccountSheet visible={accountVisible} onClose={() => setAccountVisible(false)} />
    </View>
  );
}

const styles = StyleSheet.create({
  appbar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.three,
    paddingVertical: Spacing.two,
  },
  titleBlock: {
    gap: 2,
  },
  eyebrow: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  title: {
    fontWeight: '800',
    fontSize: 19,
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: Radius.pill,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontWeight: '700',
    fontSize: 12,
  },
});
