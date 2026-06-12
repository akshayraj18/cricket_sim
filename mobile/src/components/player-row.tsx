import { Pressable, StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { PlayerDict } from '@/api/types';
import { Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

const ROLE_BADGES: Record<string, string> = {
  Wicketkeeper: 'WK',
  Batsman: 'BAT',
  'All-Rounder': 'AR',
  'Bowler (Fast)': 'BWL',
  'Bowler (Spin)': 'BWL',
};

export function roleBadge(role: string): string {
  return ROLE_BADGES[role] ?? role.slice(0, 3).toUpperCase();
}

export function PlayerRow({
  player,
  onPress,
  accentColor,
  isCaptain,
  isViceCaptain,
  isWicketkeeper,
  trailing,
  subtitle,
}: {
  player: Pick<PlayerDict, 'name' | 'role' | 'ovr' | 'batting_archetype' | 'bowling_phase'>;
  onPress?: () => void;
  accentColor?: string;
  isCaptain?: boolean;
  isViceCaptain?: boolean;
  isWicketkeeper?: boolean;
  /** Custom trailing content; defaults to OVR. */
  trailing?: React.ReactNode;
  /** Custom subtitle; defaults to role · archetype. */
  subtitle?: string;
}) {
  const theme = useTheme();
  const isBowler = player.role.includes('Bowler');

  const Wrapper = onPress ? Pressable : View;

  return (
    <Wrapper
      onPress={onPress}
      style={({ pressed }: { pressed?: boolean }) => [
        styles.row,
        { borderBottomColor: theme.border },
        pressed && onPress ? styles.pressed : null,
      ]}>
      <View style={[styles.posBadge, { backgroundColor: theme.bgElevated, borderColor: theme.border }]}>
        <ThemedText style={[styles.posBadgeText, { color: accentColor ?? theme.textDim }]}>
          {roleBadge(player.role)}
        </ThemedText>
      </View>
      <View style={styles.info}>
        <View style={styles.nameRow}>
          <ThemedText style={styles.name} numberOfLines={1}>
            {player.name}
          </ThemedText>
          {isCaptain && (
            <View style={[styles.badgeMini, { backgroundColor: accentColor ?? theme.green }]}>
              <ThemedText style={styles.badgeMiniText}>C</ThemedText>
            </View>
          )}
          {isViceCaptain && (
            <View style={[styles.badgeMini, { backgroundColor: theme.badgeBgStrong }]}>
              <ThemedText style={[styles.badgeMiniText, { color: theme.text }]}>VC</ThemedText>
            </View>
          )}
          {isWicketkeeper && (
            <View style={[styles.badgeMini, { backgroundColor: theme.badgeBgStrong }]}>
              <ThemedText style={[styles.badgeMiniText, { color: theme.text }]}>WK</ThemedText>
            </View>
          )}
        </View>
        <ThemedText themeColor="textDim" style={styles.role} numberOfLines={1}>
          {subtitle ?? `${player.role} · ${isBowler ? player.bowling_phase : player.batting_archetype}`}
        </ThemedText>
      </View>
      {trailing !== undefined ? (
        trailing
      ) : (
        <ThemedText style={[styles.ovr, { color: accentColor ?? theme.text }]}>{player.ovr}</ThemedText>
      )}
    </Wrapper>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.three,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  pressed: {
    opacity: 0.6,
  },
  posBadge: {
    width: 32,
    height: 32,
    borderRadius: Radius.sm,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  posBadgeText: {
    fontSize: 10.5,
    fontWeight: '800',
  },
  info: {
    flex: 1,
    minWidth: 0,
    gap: 1,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  name: {
    fontWeight: '700',
    fontSize: 13.5,
    flexShrink: 1,
  },
  role: {
    fontSize: 11,
  },
  ovr: {
    fontSize: 16,
    fontWeight: '800',
    minWidth: 30,
    textAlign: 'right',
  },
  badgeMini: {
    borderRadius: 5,
    paddingHorizontal: 5,
    paddingVertical: 1,
  },
  badgeMiniText: {
    fontSize: 9,
    fontWeight: '800',
    color: '#1a1404',
  },
});
