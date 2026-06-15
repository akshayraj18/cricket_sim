import { router } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  TextInput,
  View,
} from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Difficulty, DraftPoolType } from '@/api/types';
import { Radius, Spacing, TEAM_NAMES, TeamColors, getTeamAccentText } from '@/constants/theme';
import { useCareer } from '@/context/CareerContext';
import { useError } from '@/context/ErrorContext';
import { useNotifications } from '@/context/NotificationsContext';
import { useCareers } from '@/hooks/use-careers';
import { useAnalytics } from '@/observability/analytics';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { useTheme } from '@/hooks/use-theme';

const DIFFICULTIES: { value: Difficulty; label: string }[] = [
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' },
];

const DRAFT_POOLS: { value: DraftPoolType; label: string; description: string }[] = [
  {
    value: 'rosters2026',
    label: '2026 Rosters (No Draft)',
    description: "Skip the draft and start with your franchise's real 2026 squad.",
  },
  {
    value: 'current',
    label: '2026 Rosters (Mega Draft)',
    description: 'Draft from the pool of real 2026 IPL players.',
  },
  {
    value: 'alltime',
    label: 'All-Time IPL Greats (Mega Draft)',
    description: 'Draft from the greatest players across IPL history.',
  },
];

export default function NewCareerScreen() {
  const theme = useTheme();
  const scheme = useColorScheme();
  const { createCareer } = useCareers();
  const { setActiveCareerId } = useCareer();
  const { promptPermission } = useNotifications();
  const { showError } = useError();
  const analytics = useAnalytics();

  const [name, setName] = useState('');
  const [team, setTeam] = useState(TEAM_NAMES[0]);
  const [difficulty, setDifficulty] = useState<Difficulty>('medium');
  const [draftPoolType, setDraftPoolType] = useState<DraftPoolType>('rosters2026');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onCreate = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const career = await createCareer({
        name: name.trim() || `${team} Career`,
        user_team_name: team,
        difficulty,
        draft_pool_type: draftPoolType,
      });
      analytics.capture('career_created', { team, difficulty, draft_pool: draftPoolType });
      setActiveCareerId(career.id);
      // First career created → ask to enable re-engagement reminders (one-time).
      promptPermission();
      router.replace('/(tabs)/season');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create career');
      showError(err, { onRetry: onCreate });
      setSubmitting(false);
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.field}>
          <ThemedText themeColor="textFaint" style={styles.label}>
            Career Name
          </ThemedText>
          <TextInput
            value={name}
            onChangeText={setName}
            placeholder={`${team} Career`}
            placeholderTextColor={theme.textFaint}
            style={[
              styles.input,
              { backgroundColor: theme.bgCard, borderColor: theme.border, color: theme.text },
            ]}
          />
        </View>

        <View style={styles.field}>
          <ThemedText themeColor="textFaint" style={styles.label}>
            Choose Franchise
          </ThemedText>
          <View style={styles.teamGrid}>
            {TEAM_NAMES.map((teamName) => {
              const meta = TeamColors[teamName];
              const selected = teamName === team;
              const accentText = getTeamAccentText(teamName, scheme === 'dark' ? 'dark' : 'light');
              return (
                <Pressable
                  key={teamName}
                  onPress={() => setTeam(teamName)}
                  style={({ pressed }) => [
                    styles.teamChip,
                    {
                      backgroundColor: theme.bgCard,
                      borderColor: selected ? theme.green : theme.border,
                    },
                    pressed && styles.pressed,
                  ]}>
                  <ThemedText style={[styles.teamAbbr, { color: accentText }]}>{meta.abbr}</ThemedText>
                  <ThemedText themeColor="textDim" style={styles.teamName} numberOfLines={1}>
                    {teamName}
                  </ThemedText>
                </Pressable>
              );
            })}
          </View>
        </View>

        <View style={styles.field}>
          <ThemedText themeColor="textFaint" style={styles.label}>
            Franchise Difficulty
          </ThemedText>
          <View style={styles.segRow}>
            {DIFFICULTIES.map((d) => {
              const selected = d.value === difficulty;
              return (
                <Pressable
                  key={d.value}
                  onPress={() => setDifficulty(d.value)}
                  style={({ pressed }) => [
                    styles.segItem,
                    {
                      backgroundColor: selected ? theme.green : theme.bgCard,
                      borderColor: selected ? theme.green : theme.border,
                    },
                    pressed && styles.pressed,
                  ]}>
                  <ThemedText
                    style={[styles.segLabel, { color: selected ? '#1a1404' : theme.text }]}>
                    {d.label}
                  </ThemedText>
                </Pressable>
              );
            })}
          </View>
        </View>

        <View style={styles.field}>
          <ThemedText themeColor="textFaint" style={styles.label}>
            Draft Pool
          </ThemedText>
          <View style={styles.poolList}>
            {DRAFT_POOLS.map((pool) => {
              const selected = pool.value === draftPoolType;
              return (
                <Pressable
                  key={pool.value}
                  onPress={() => setDraftPoolType(pool.value)}
                  style={({ pressed }) => [
                    styles.poolItem,
                    {
                      backgroundColor: theme.bgCard,
                      borderColor: selected ? theme.green : theme.border,
                    },
                    pressed && styles.pressed,
                  ]}>
                  <ThemedText style={styles.poolLabel}>{pool.label}</ThemedText>
                  <ThemedText themeColor="textDim" style={styles.poolDescription}>
                    {pool.description}
                  </ThemedText>
                </Pressable>
              );
            })}
          </View>
        </View>

        {error && (
          <ThemedText themeColor="red" style={styles.error}>
            {error}
          </ThemedText>
        )}

        <Pressable
          onPress={onCreate}
          disabled={submitting}
          style={({ pressed }) => [
            styles.createButton,
            { backgroundColor: theme.green, opacity: pressed || submitting ? 0.85 : 1 },
          ]}>
          {submitting ? (
            <ActivityIndicator color="#1a1404" />
          ) : (
            <ThemedText style={styles.createButtonText}>Create New League</ThemedText>
          )}
        </Pressable>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: Spacing.three,
    gap: Spacing.four,
    paddingBottom: Spacing.six,
  },
  field: {
    gap: Spacing.two,
  },
  label: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  input: {
    borderWidth: 1,
    borderRadius: Radius.sm,
    paddingHorizontal: Spacing.three,
    paddingVertical: 12,
    fontSize: 15,
  },
  teamGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.two,
  },
  teamChip: {
    width: '31%',
    borderWidth: 1,
    borderRadius: Radius.sm,
    paddingVertical: Spacing.two,
    paddingHorizontal: Spacing.two,
    alignItems: 'center',
    gap: 2,
  },
  teamAbbr: {
    fontWeight: '800',
    fontSize: 14,
  },
  teamName: {
    fontSize: 9.5,
    textAlign: 'center',
  },
  pressed: {
    opacity: 0.7,
  },
  segRow: {
    flexDirection: 'row',
    gap: Spacing.two,
  },
  segItem: {
    flex: 1,
    borderWidth: 1,
    borderRadius: Radius.sm,
    paddingVertical: 10,
    alignItems: 'center',
  },
  segLabel: {
    fontWeight: '700',
    fontSize: 13,
  },
  poolList: {
    gap: Spacing.two,
  },
  poolItem: {
    borderWidth: 1,
    borderRadius: Radius.md,
    padding: Spacing.three,
    gap: 4,
  },
  poolLabel: {
    fontWeight: '700',
    fontSize: 13.5,
  },
  poolDescription: {
    fontSize: 12,
    lineHeight: 17,
  },
  error: {
    textAlign: 'center',
  },
  createButton: {
    borderRadius: Radius.sm,
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  createButtonText: {
    fontWeight: '700',
    fontSize: 15,
    color: '#1a1404',
  },
});
