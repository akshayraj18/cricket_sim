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
import { CareerMode, Competition, Difficulty, DraftPoolType, MatchFormat } from '@/api/types';
import {
  InternationalTeamColors,
  INTERNATIONAL_TEAM_NAMES,
  Radius,
  Spacing,
  TEAM_NAMES,
  TeamColors,
  getTeamAccentText,
} from '@/constants/theme';
import { useCareer } from '@/context/CareerContext';
import { useError } from '@/context/ErrorContext';
import { useNotifications } from '@/context/NotificationsContext';
import { useCareers } from '@/hooks/use-careers';
import { useAnalytics } from '@/observability/analytics';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { useTheme } from '@/hooks/use-theme';

type Step = 'competition' | 'format' | 'mode' | 'opponent' | 'team' | 'difficulty' | 'confirm';

const FORMATS: { value: MatchFormat; label: string; desc: string }[] = [
  { value: 't20', label: 'T20', desc: '20 overs per side' },
  { value: 'odi', label: 'ODI', desc: '50 overs per side' },
  { value: 'test', label: 'Test', desc: '5-day matches, 2 innings each' },
];

const SERIES_LENGTHS = [
  { value: 1, label: '1 Match' },
  { value: 3, label: 'Best of 3' },
  { value: 5, label: 'Best of 5' },
];

const DIFFICULTIES: { value: Difficulty; label: string }[] = [
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' },
];

export default function NewCareerScreen() {
  const theme = useTheme();
  const scheme = useColorScheme();
  const { createCareer } = useCareers();
  const { setActiveCareerId } = useCareer();
  const { promptPermission } = useNotifications();
  const { showError } = useError();
  const analytics = useAnalytics();

  const [step, setStep] = useState<Step>('competition');
  const [competition, setCompetition] = useState<Competition>('ipl');
  const [matchFormat, setMatchFormat] = useState<MatchFormat>('t20');
  const [careerMode, setCareerMode] = useState<CareerMode>('league');
  const [seriesLength, setSeriesLength] = useState(3);
  const [team, setTeam] = useState(TEAM_NAMES[0]);
  const [intlTeam, setIntlTeam] = useState(INTERNATIONAL_TEAM_NAMES[0]);
  const [opponentTeam, setOpponentTeam] = useState(INTERNATIONAL_TEAM_NAMES[1]);
  const [difficulty, setDifficulty] = useState<Difficulty>('medium');
  const [name, setName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const userTeamName = competition === 'ipl' ? team : intlTeam;

  const teamColors = competition === 'ipl' ? TeamColors : InternationalTeamColors;
  const teamNames = competition === 'ipl' ? TEAM_NAMES : INTERNATIONAL_TEAM_NAMES;

  const defaultName = () => {
    if (competition === 'international' && careerMode === 'bilateral') {
      return `${intlTeam} vs ${opponentTeam}`;
    }
    return `${userTeamName} Career`;
  };

  const onCreate = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const draftPool: DraftPoolType =
        competition === 'international' ? 'international_current' :
        competition === 'ipl' ? 'rosters2026' : 'current';

      const career = await createCareer({
        name: name.trim() || defaultName(),
        user_team_name: userTeamName,
        difficulty,
        draft_pool_type: draftPool,
        competition,
        match_format: matchFormat,
        career_mode: careerMode,
        series_length: careerMode === 'bilateral' ? seriesLength : null,
        opponent_name: careerMode === 'bilateral' ? opponentTeam : null,
      });
      analytics.capture('career_created', {
        competition,
        format: matchFormat,
        mode: careerMode,
        team: userTeamName,
        difficulty,
      });
      setActiveCareerId(career.id);
      promptPermission();
      router.replace('/(tabs)/season');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create career');
      showError(err, { onRetry: onCreate });
      setSubmitting(false);
    }
  };

  const goBack = () => {
    if (step === 'format') { setStep('competition'); return; }
    if (step === 'mode') { setStep('format'); return; }
    if (step === 'opponent') { setStep('mode'); return; }
    if (step === 'team') {
      if (competition === 'international' && careerMode === 'bilateral') { setStep('opponent'); return; }
      if (competition === 'international') { setStep('mode'); return; }
      setStep('competition');
      return;
    }
    if (step === 'difficulty') { setStep('team'); return; }
    if (step === 'confirm') { setStep('difficulty'); return; }
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {step !== 'competition' && (
          <Pressable onPress={goBack} style={styles.backBtn}>
            <ThemedText themeColor="textDim" style={styles.backLabel}>← Back</ThemedText>
          </Pressable>
        )}

        {/* Step 1: Competition */}
        {step === 'competition' && (
          <View style={styles.field}>
            <ThemedText themeColor="textFaint" style={styles.label}>Competition</ThemedText>
            <View style={styles.cardList}>
              <Pressable
                onPress={() => { setCompetition('ipl'); setCareerMode('league'); setStep('team'); }}
                style={({ pressed }) => [styles.bigCard, { backgroundColor: theme.bgCard, borderColor: theme.border }, pressed && styles.pressed]}>
                <ThemedText style={styles.bigCardTitle}>IPL Franchise</ThemedText>
                <ThemedText themeColor="textDim" style={styles.bigCardDesc}>
                  Manage a T20 franchise through drafts, seasons, and playoffs.
                </ThemedText>
              </Pressable>
              <Pressable
                onPress={() => { setCompetition('international'); setStep('format'); }}
                style={({ pressed }) => [styles.bigCard, { backgroundColor: theme.bgCard, borderColor: theme.border }, pressed && styles.pressed]}>
                <ThemedText style={styles.bigCardTitle}>International</ThemedText>
                <ThemedText themeColor="textDim" style={styles.bigCardDesc}>
                  Lead a national team in T20, ODI, or Test cricket — tournament or bilateral series.
                </ThemedText>
              </Pressable>
            </View>
          </View>
        )}

        {/* Step 2: Format (international only) */}
        {step === 'format' && (
          <View style={styles.field}>
            <ThemedText themeColor="textFaint" style={styles.label}>Match Format</ThemedText>
            <View style={styles.segRow}>
              {FORMATS.map((f) => {
                const sel = matchFormat === f.value;
                return (
                  <Pressable
                    key={f.value}
                    onPress={() => setMatchFormat(f.value)}
                    style={({ pressed }) => [
                      styles.segItem,
                      { backgroundColor: sel ? theme.green : theme.bgCard, borderColor: sel ? theme.green : theme.border },
                      pressed && styles.pressed,
                    ]}>
                    <ThemedText style={[styles.segLabel, { color: sel ? '#1a1404' : theme.text }]}>{f.label}</ThemedText>
                    <ThemedText style={[styles.segDesc, { color: sel ? '#1a1404' : theme.textDim }]}>{f.desc}</ThemedText>
                  </Pressable>
                );
              })}
            </View>
            <Pressable
              onPress={() => setStep('mode')}
              style={({ pressed }) => [styles.nextBtn, { backgroundColor: theme.green, opacity: pressed ? 0.85 : 1 }]}>
              <ThemedText style={styles.nextBtnText}>Next</ThemedText>
            </Pressable>
          </View>
        )}

        {/* Step 3: Career Mode (international only) */}
        {step === 'mode' && (
          <View style={styles.field}>
            <ThemedText themeColor="textFaint" style={styles.label}>Career Mode</ThemedText>
            <View style={styles.cardList}>
              <Pressable
                onPress={() => { setCareerMode('tournament'); setStep('team'); }}
                style={({ pressed }) => [styles.bigCard, { backgroundColor: theme.bgCard, borderColor: theme.border }, pressed && styles.pressed]}>
                <ThemedText style={styles.bigCardTitle}>World Tournament</ThemedText>
                <ThemedText themeColor="textDim" style={styles.bigCardDesc}>
                  Round-robin against all 9 nations, then playoffs. {matchFormat === 'test' ? 'Top 2 reach the Final.' : 'Top 4 reach the semis.'}
                </ThemedText>
              </Pressable>
              <Pressable
                onPress={() => { setCareerMode('bilateral'); setStep('opponent'); }}
                style={({ pressed }) => [styles.bigCard, { backgroundColor: theme.bgCard, borderColor: theme.border }, pressed && styles.pressed]}>
                <ThemedText style={styles.bigCardTitle}>Bilateral Series</ThemedText>
                <ThemedText themeColor="textDim" style={styles.bigCardDesc}>
                  Pick one opponent and play a 1, 3, or 5-match series.
                </ThemedText>
              </Pressable>
            </View>
          </View>
        )}

        {/* Step 3b: Bilateral options (opponent + series length) */}
        {step === 'opponent' && (
          <View style={styles.field}>
            <ThemedText themeColor="textFaint" style={styles.label}>Series Length</ThemedText>
            <View style={styles.segRow}>
              {SERIES_LENGTHS.map((sl) => {
                const sel = seriesLength === sl.value;
                return (
                  <Pressable
                    key={sl.value}
                    onPress={() => setSeriesLength(sl.value)}
                    style={({ pressed }) => [
                      styles.segItem,
                      { backgroundColor: sel ? theme.green : theme.bgCard, borderColor: sel ? theme.green : theme.border },
                      pressed && styles.pressed,
                    ]}>
                    <ThemedText style={[styles.segLabel, { color: sel ? '#1a1404' : theme.text }]}>{sl.label}</ThemedText>
                  </Pressable>
                );
              })}
            </View>
            <ThemedText themeColor="textFaint" style={[styles.label, { marginTop: Spacing.three }]}>Opponent</ThemedText>
            <View style={styles.teamGrid}>
              {INTERNATIONAL_TEAM_NAMES.filter((n) => n !== intlTeam).map((n) => {
                const meta = InternationalTeamColors[n];
                const sel = n === opponentTeam;
                const accentText = getTeamAccentText(meta, scheme === 'dark' ? 'dark' : 'light');
                return (
                  <Pressable
                    key={n}
                    onPress={() => setOpponentTeam(n)}
                    style={({ pressed }) => [
                      styles.teamChip,
                      { backgroundColor: theme.bgCard, borderColor: sel ? theme.green : theme.border },
                      pressed && styles.pressed,
                    ]}>
                    <ThemedText style={[styles.teamAbbr, { color: accentText }]}>{meta.abbr}</ThemedText>
                    <ThemedText themeColor="textDim" style={styles.teamName} numberOfLines={1}>{n}</ThemedText>
                  </Pressable>
                );
              })}
            </View>
            <Pressable
              onPress={() => setStep('team')}
              style={({ pressed }) => [styles.nextBtn, { backgroundColor: theme.green, opacity: pressed ? 0.85 : 1 }]}>
              <ThemedText style={styles.nextBtnText}>Next</ThemedText>
            </Pressable>
          </View>
        )}

        {/* Step 4: Team picker */}
        {step === 'team' && (
          <View style={styles.field}>
            <ThemedText themeColor="textFaint" style={styles.label}>
              {competition === 'ipl' ? 'Choose Franchise' : 'Choose Nation'}
            </ThemedText>
            <View style={styles.teamGrid}>
              {teamNames
                .filter((n) => !(careerMode === 'bilateral' && n === opponentTeam))
                .map((n) => {
                  const meta = teamColors[n];
                  const sel = n === (competition === 'ipl' ? team : intlTeam);
                  const accentText = getTeamAccentText(meta, scheme === 'dark' ? 'dark' : 'light');
                  return (
                    <Pressable
                      key={n}
                      onPress={() => competition === 'ipl' ? setTeam(n) : setIntlTeam(n)}
                      style={({ pressed }) => [
                        styles.teamChip,
                        { backgroundColor: theme.bgCard, borderColor: sel ? theme.green : theme.border },
                        pressed && styles.pressed,
                      ]}>
                      <ThemedText style={[styles.teamAbbr, { color: accentText }]}>{meta.abbr}</ThemedText>
                      <ThemedText themeColor="textDim" style={styles.teamName} numberOfLines={1}>{n}</ThemedText>
                    </Pressable>
                  );
                })}
            </View>
            <Pressable
              onPress={() => setStep('difficulty')}
              style={({ pressed }) => [styles.nextBtn, { backgroundColor: theme.green, opacity: pressed ? 0.85 : 1 }]}>
              <ThemedText style={styles.nextBtnText}>Next</ThemedText>
            </Pressable>
          </View>
        )}

        {/* Step 5: Difficulty */}
        {step === 'difficulty' && (
          <View style={styles.field}>
            <ThemedText themeColor="textFaint" style={styles.label}>Difficulty</ThemedText>
            <View style={styles.segRow}>
              {DIFFICULTIES.map((d) => {
                const sel = d.value === difficulty;
                return (
                  <Pressable
                    key={d.value}
                    onPress={() => setDifficulty(d.value)}
                    style={({ pressed }) => [
                      styles.segItem,
                      { backgroundColor: sel ? theme.green : theme.bgCard, borderColor: sel ? theme.green : theme.border },
                      pressed && styles.pressed,
                    ]}>
                    <ThemedText style={[styles.segLabel, { color: sel ? '#1a1404' : theme.text }]}>{d.label}</ThemedText>
                  </Pressable>
                );
              })}
            </View>
            <ThemedText themeColor="textFaint" style={[styles.label, { marginTop: Spacing.three }]}>Career Name (optional)</ThemedText>
            <TextInput
              value={name}
              onChangeText={setName}
              placeholder={defaultName()}
              placeholderTextColor={theme.textFaint}
              style={[styles.input, { backgroundColor: theme.bgCard, borderColor: theme.border, color: theme.text }]}
            />
            {error && (
              <ThemedText themeColor="red" style={styles.error}>{error}</ThemedText>
            )}
            <Pressable
              onPress={onCreate}
              disabled={submitting}
              style={({ pressed }) => [styles.nextBtn, { backgroundColor: theme.green, opacity: pressed || submitting ? 0.85 : 1 }]}>
              {submitting ? (
                <ActivityIndicator color="#1a1404" />
              ) : (
                <ThemedText style={styles.nextBtnText}>
                  {competition === 'ipl' ? 'Create New League' : careerMode === 'bilateral' ? 'Start Series' : 'Start Tournament'}
                </ThemedText>
              )}
            </Pressable>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: Spacing.three, gap: Spacing.four, paddingBottom: Spacing.six },
  backBtn: { paddingVertical: Spacing.one },
  backLabel: { fontSize: 14 },
  field: { gap: Spacing.two },
  label: { fontSize: 11, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 1 },
  input: {
    borderWidth: 1,
    borderRadius: Radius.sm,
    paddingHorizontal: Spacing.three,
    paddingVertical: 12,
    fontSize: 15,
  },
  cardList: { gap: Spacing.two },
  bigCard: {
    borderWidth: 1,
    borderRadius: Radius.md,
    padding: Spacing.three,
    gap: 6,
  },
  bigCardTitle: { fontWeight: '700', fontSize: 15 },
  bigCardDesc: { fontSize: 13, lineHeight: 19 },
  teamGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.two },
  teamChip: {
    width: '31%',
    borderWidth: 1,
    borderRadius: Radius.sm,
    paddingVertical: Spacing.two,
    paddingHorizontal: Spacing.two,
    alignItems: 'center',
    gap: 2,
  },
  teamAbbr: { fontWeight: '800', fontSize: 14 },
  teamName: { fontSize: 9.5, textAlign: 'center' },
  segRow: { flexDirection: 'row', gap: Spacing.two },
  segItem: {
    flex: 1,
    borderWidth: 1,
    borderRadius: Radius.sm,
    paddingVertical: 10,
    alignItems: 'center',
    gap: 2,
  },
  segLabel: { fontWeight: '700', fontSize: 13 },
  segDesc: { fontSize: 10, textAlign: 'center' },
  nextBtn: {
    borderRadius: Radius.sm,
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: Spacing.two,
  },
  nextBtnText: { fontWeight: '700', fontSize: 15, color: '#1a1404' },
  pressed: { opacity: 0.7 },
  error: { textAlign: 'center' },
});
