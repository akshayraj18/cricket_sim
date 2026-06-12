import { SymbolView } from 'expo-symbols';
import { Pressable, StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { CareerSummary } from '@/api/types';
import { Radius, Spacing, TeamColors, getTeamAccentText } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

function formatStatus(career: CareerSummary): string {
  const seasonLabel = `${career.season_year} Season`;
  const seasonsLabel =
    career.completed_seasons > 0
      ? `${career.completed_seasons} title${career.completed_seasons === 1 ? '' : 's'}`
      : null;

  return [seasonLabel, career.status_message, seasonsLabel].filter(Boolean).join(' · ');
}

export function CareerCard({
  career,
  active,
  onPress,
  onDelete,
}: {
  career: CareerSummary;
  active?: boolean;
  onPress: () => void;
  onDelete?: () => void;
}) {
  const theme = useTheme();
  const scheme = useColorScheme();
  const team = TeamColors[career.user_team_name];
  const accentText = getTeamAccentText(career.user_team_name, scheme === 'dark' ? 'dark' : 'light');

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [pressed && styles.pressed]}>
      <View
        style={[
          styles.card,
          { backgroundColor: theme.bgCard, borderColor: active ? theme.green : theme.border },
        ]}>
        <View style={[styles.crest, { backgroundColor: theme.bg, borderColor: theme.border }]}>
          <ThemedText style={[styles.crestText, { color: accentText }]}>
            {team?.abbr ?? career.user_team_name.slice(0, 3).toUpperCase()}
          </ThemedText>
        </View>
        <View style={styles.meta}>
          <ThemedText style={styles.name} numberOfLines={1}>
            {career.name}
          </ThemedText>
          <ThemedText themeColor="textDim" style={styles.sub} numberOfLines={1}>
            {formatStatus(career)}
          </ThemedText>
        </View>
        {active ? (
          <SymbolView
            tintColor={theme.green}
            name={{ ios: 'checkmark.circle.fill', web: 'check_circle' }}
            size={18}
          />
        ) : (
          <SymbolView
            tintColor={theme.textFaint}
            name={{ ios: 'chevron.right', web: 'chevron_right' }}
            size={14}
          />
        )}
        {onDelete ? (
          <Pressable hitSlop={10} onPress={onDelete} style={styles.deleteBtn}>
            <SymbolView tintColor={theme.red} name={{ ios: 'trash', web: 'delete' }} size={16} />
          </Pressable>
        ) : null}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  pressed: {
    opacity: 0.7,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.three,
    borderRadius: Radius.md,
    borderWidth: 1,
    padding: Spacing.three,
  },
  crest: {
    width: 44,
    height: 44,
    borderRadius: Radius.sm,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  crestText: {
    fontWeight: '800',
    fontSize: 13,
  },
  meta: {
    flex: 1,
    gap: 2,
  },
  name: {
    fontWeight: '700',
    fontSize: 15,
  },
  sub: {
    fontSize: 12,
  },
  deleteBtn: {
    paddingHorizontal: 4,
    paddingVertical: 4,
  },
});
