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
  WorldTeamColors,
  WORLD_TEAM_NAMES,
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
import { useLayout } from '@/hooks/use-layout';
import { useTheme } from '@/hooks/use-theme';

type Step = 'competition' | 'intl_options' | 'opponent' | 'team' | 'difficulty';

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
  const { contentContainerStyle } = useLayout();
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
  const [worldTeam, setWorldTeam] = useState(WORLD_TEAM_NAMES[0]);
  const [opponentTeam, setOpponentTeam] = useState(INTERNATIONAL_TEAM_NAMES[1]);
  const [difficulty, setDifficulty] = useState<Difficulty>('medium');
  const [name, setName] = useState('');
  const [draftPoolMode, setDraftPoolMode] = useState<'current' | 'alltime'>('current');
  /**
   * Squad choice for the Indian T20 league: start with the 2026 squads, or
   * draft the whole pool from scratch. Defaults to no-draft so a first career
   * reaches an actual match quickly.
   */
  const [iplPool, setIplPool] = useState<'rosters2026' | 'current'>('rosters2026');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // All-Time Greats tournament → city franchises (WorldTeam). Everything else → national teams.
  const isWorldDraft = competition === 'international' && careerMode === 'tournament' && draftPoolMode === 'alltime';
  const userTeamName = competition === 'ipl' ? team : isWorldDraft ? worldTeam : intlTeam;

  const teamColors = competition === 'ipl' ? TeamColors : isWorldDraft ? WorldTeamColors : InternationalTeamColors;
  const teamNames = competition === 'ipl' ? TEAM_NAMES : isWorldDraft ? WORLD_TEAM_NAMES : INTERNATIONAL_TEAM_NAMES;

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
        competition === 'ipl' ? iplPool :
        draftPoolMode === 'alltime' ? (
          matchFormat === 'odi' ? 'alltime_odi' :
          matchFormat === 'test' ? 'alltime_test' :
          'alltime_t20_intl'
        ) : 'international_current';

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
    if (step === 'intl_options') { setStep('competition'); return; }
    if (step === 'opponent') { setStep('intl_options'); return; }
    if (step === 'team') {
      if (competition === 'international' && careerMode === 'bilateral') { setStep('opponent'); return; }
      if (competition === 'international') { setStep('intl_options'); return; }
      setStep('competition');
      return;
    }
    if (step === 'difficulty') { setStep('team'); return; }
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      <ScrollView contentContainerStyle={[styles.content, contentContainerStyle]} keyboardShouldPersistTaps="handled">
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
                <ThemedText style={styles.bigCardTitle}>Indian T20 League</ThemedText>
                <ThemedText themeColor="textDim" style={styles.bigCardDesc}>
                  Manage a T20 franchise through drafts, seasons, and playoffs.
                </ThemedText>
              </Pressable>
              <Pressable
                onPress={() => { setCompetition('international'); setCareerMode('tournament'); setStep('intl_options'); }}
                style={({ pressed }) => [styles.bigCard, { backgroundColor: theme.bgCard, borderColor: theme.border }, pressed && styles.pressed]}>
                <ThemedText style={styles.bigCardTitle}>International</ThemedText>
                <ThemedText themeColor="textDim" style={styles.bigCardDesc}>
                  Lead a national team in T20, ODI, or Test cricket — tournament or bilateral series.
                </ThemedText>
              </Pressable>
            </View>
          </View>
        )}

        {/* Step 2: International options — format + mode + squad on one page */}
        {step === 'intl_options' && (
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

            <ThemedText themeColor="textFaint" style={[styles.label, { marginTop: Spacing.three }]}>Career Mode</ThemedText>
            <View style={styles.segRow}>
              {[
                { value: 'tournament' as CareerMode, label: 'World Tournament', desc: matchFormat === 'test' ? 'Top 2 → Final' : 'Top 4 → Semis + Final' },
                { value: 'bilateral' as CareerMode, label: 'Bilateral Series', desc: 'vs one opponent' },
              ].map((m) => {
                const sel = careerMode === m.value;
                return (
                  <Pressable
                    key={m.value}
                    onPress={() => setCareerMode(m.value)}
                    style={({ pressed }) => [
                      styles.segItem,
                      { backgroundColor: sel ? theme.green : theme.bgCard, borderColor: sel ? theme.green : theme.border },
                      pressed && styles.pressed,
                    ]}>
                    <ThemedText style={[styles.segLabel, { color: sel ? '#1a1404' : theme.text }]}>{m.label}</ThemedText>
                    <ThemedText style={[styles.segDesc, { color: sel ? '#1a1404' : theme.textDim }]}>{m.desc}</ThemedText>
                  </Pressable>
                );
              })}
            </View>

            <ThemedText themeColor="textFaint" style={[styles.label, { marginTop: Spacing.three }]}>Squad</ThemedText>
            <View style={styles.segRow}>
              {[
                { value: 'current' as const, label: 'Current Roster', desc: 'Real 2026 squads, no draft' },
                { value: 'alltime' as const, label: 'All-Time Greats', desc: 'Mega draft, 350+ legends' },
              ].map((s) => {
                const sel = draftPoolMode === s.value;
                return (
                  <Pressable
                    key={s.value}
                    onPress={() => setDraftPoolMode(s.value)}
                    style={({ pressed }) => [
                      styles.segItem,
                      { backgroundColor: sel ? theme.green : theme.bgCard, borderColor: sel ? theme.green : theme.border },
                      pressed && styles.pressed,
                    ]}>
                    <ThemedText style={[styles.segLabel, { color: sel ? '#1a1404' : theme.text }]}>{s.label}</ThemedText>
                    <ThemedText style={[styles.segDesc, { color: sel ? '#1a1404' : theme.textDim }]}>{s.desc}</ThemedText>
                  </Pressable>
                );
              })}
            </View>

            <Pressable
              onPress={() => setStep(careerMode === 'bilateral' ? 'opponent' : 'team')}
              style={({ pressed }) => [styles.nextBtn, { backgroundColor: theme.green, opacity: pressed ? 0.85 : 1 }]}>
              <ThemedText style={styles.nextBtnText}>Next</ThemedText>
            </Pressable>
          </View>
        )}

        {/* Step 3c: Bilateral setup — your team, opponent, and series length on one screen */}
        {step === 'opponent' && (
          <View style={styles.field}>
            <ThemedText themeColor="textFaint" style={styles.label}>Your Nation</ThemedText>
            <View style={styles.teamGrid}>
              {INTERNATIONAL_TEAM_NAMES.map((n) => {
                const meta = InternationalTeamColors[n];
                const sel = n === intlTeam;
                const accentText = getTeamAccentText(meta, scheme === 'dark' ? 'dark' : 'light');
                return (
                  <Pressable
                    key={n}
                    onPress={() => {
                      setIntlTeam(n);
                      if (n === opponentTeam) {
                        setOpponentTeam(INTERNATIONAL_TEAM_NAMES.find((o) => o !== n) ?? opponentTeam);
                      }
                    }}
                    style={({ pressed }) => [
                      styles.teamChip,
                      { backgroundColor: sel ? `${meta.primary}33` : theme.bgCard, borderColor: sel ? theme.green : theme.border, borderWidth: sel ? 2 : 1 },
                      pressed && styles.pressed,
                    ]}>
                    <ThemedText style={[styles.teamAbbr, { color: accentText }]}>{meta.abbr}</ThemedText>
                    <ThemedText themeColor="textDim" style={styles.teamName} numberOfLines={1}>{n}</ThemedText>
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
                      { backgroundColor: sel ? `${meta.primary}33` : theme.bgCard, borderColor: sel ? theme.green : theme.border, borderWidth: sel ? 2 : 1 },
                      pressed && styles.pressed,
                    ]}>
                    <ThemedText style={[styles.teamAbbr, { color: accentText }]}>{meta.abbr}</ThemedText>
                    <ThemedText themeColor="textDim" style={styles.teamName} numberOfLines={1}>{n}</ThemedText>
                  </Pressable>
                );
              })}
            </View>

            <ThemedText themeColor="textFaint" style={[styles.label, { marginTop: Spacing.three }]}>Series Length</ThemedText>
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

            <Pressable
              onPress={() => setStep('difficulty')}
              style={({ pressed }) => [styles.nextBtn, { backgroundColor: theme.green, opacity: pressed ? 0.85 : 1 }]}>
              <ThemedText style={styles.nextBtnText}>Next</ThemedText>
            </Pressable>
          </View>
        )}

        {/* Step 4: Team picker */}
        {step === 'team' && (
          <View style={styles.field}>
            <ThemedText themeColor="textFaint" style={styles.label}>
              {competition === 'ipl' || isWorldDraft ? 'Choose Franchise' : 'Choose Nation'}
            </ThemedText>
            <View style={styles.teamGrid}>
              {teamNames.map((n) => {
                const meta = teamColors[n];
                const sel = n === (competition === 'ipl' ? team : isWorldDraft ? worldTeam : intlTeam);
                const accentText = getTeamAccentText(meta, scheme === 'dark' ? 'dark' : 'light');
                return (
                  <Pressable
                    key={n}
                    onPress={() => competition === 'ipl' ? setTeam(n) : isWorldDraft ? setWorldTeam(n) : setIntlTeam(n)}
                    style={({ pressed }) => [
                      styles.teamChip,
                      { backgroundColor: sel ? `${meta.primary}33` : theme.bgCard, borderColor: sel ? theme.green : theme.border, borderWidth: sel ? 2 : 1 },
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
            {competition === 'ipl' && (
              <>
                <ThemedText themeColor="textFaint" style={[styles.label, { marginTop: Spacing.three }]}>Squad</ThemedText>
                <View style={styles.segRow}>
                  {[
                    // Kept short deliberately: these cards are ~181pt wide, and
                    // the longer copy measured 181-187pt, so it wrapped to a
                    // third line with an orphaned word.
                    { value: 'rosters2026' as const, label: 'Current Roster', desc: 'Your 2026 squad' },
                    { value: 'current' as const, label: 'Mega Draft', desc: 'Draft the full pool' },
                  ].map((sq) => {
                    const sel = iplPool === sq.value;
                    return (
                      <Pressable
                        key={sq.value}
                        onPress={() => setIplPool(sq.value)}
                        style={({ pressed }) => [
                          styles.segItem,
                          { backgroundColor: sel ? theme.green : theme.bgCard, borderColor: sel ? theme.green : theme.border },
                          pressed && styles.pressed,
                        ]}>
                        <ThemedText style={[styles.segLabel, { color: sel ? '#1a1404' : theme.text }]}>{sq.label}</ThemedText>
                        <ThemedText style={[styles.segDesc, { color: sel ? '#1a1404' : theme.textDim }]}>{sq.desc}</ThemedText>
                      </Pressable>
                    );
                  })}
                </View>
              </>
            )}
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
