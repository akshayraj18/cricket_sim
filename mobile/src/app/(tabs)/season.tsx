import { useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useLayout } from '@/hooks/use-layout';

import { liveMatchApi } from '@/api/liveMatch';
import { seasonApi } from '@/api/season';
import { LeaguePayload, MatchCard, PlayoffMatch, ScheduleFixture } from '@/api/types';
import { DraftHub } from '@/components/draft-hub';
import { NoActiveCareer } from '@/components/empty-state';
import { LiveMatchHub } from '@/components/live-match-hub';
import { MatchScorecard } from '@/components/match-scorecard';
import { RetentionHub } from '@/components/retention-hub';
import { ScreenHeader } from '@/components/screen-header';
import { ThemedText } from '@/components/themed-text';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Dropdown, DropdownOption } from '@/components/ui/dropdown';
import { Pill } from '@/components/ui/pill';
import { SegmentedControl } from '@/components/ui/segmented-control';
import { ContentBottomInset, getTeamBackground, getTeamSwatch, GOLD, Spacing, TeamColors, teamAbbr } from '@/constants/theme';
import { useCareer } from '@/context/CareerContext';
import { useError } from '@/context/ErrorContext';
import { useLeague } from '@/context/LeagueContext';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { useTheme } from '@/hooks/use-theme';

export default function SeasonScreen() {
  const theme = useTheme();
  const { contentContainerStyle } = useLayout();
  const { showError } = useError();
  const { activeCareerId, activeCareer } = useCareer();
  const { payload, loading, error, refresh, setPayload } = useLeague();
  const [viewedScorecard, setViewedScorecard] = useState<MatchCard | null>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const team = useMemo(
    () => payload?.teams.find((t) => t.name === payload.user_team),
    [payload]
  );
  // Filled surfaces (scoreboard, primary match buttons) take the user team's
  // color. Route it through getTeamBackground rather than the raw payload
  // primary: that vets the color for legibility (skipping near-white/gray
  // identity colors) and guarantees white text stays readable. Fall back to
  // the user_team name directly so the accent still resolves during the brief
  // windows where `team` hasn't been matched in the payload yet — only a truly
  // unknown team lands on the neutral green default. The Button picks legible
  // foreground text via contrast.
  const accent = getTeamBackground(team?.name ?? payload?.user_team ?? '');

  if (!activeCareerId) {
    return (
      <View style={[styles.container, { backgroundColor: theme.bg }]}>
        <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
          <ScreenHeader title="Match Centre" />
          <NoActiveCareer />
        </SafeAreaView>
      </View>
    );
  }

  const wrap = async (fn: () => Promise<LeaguePayload>) => {
    setBusy(true);
    setActionError(null);
    try {
      const next = await fn();
      setPayload(next);
      setViewedScorecard(null);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Action failed');
      showError(err, { onRetry: () => wrap(fn) });
    } finally {
      setBusy(false);
    }
  };

  const beginMatch = () =>
    wrap(async () => {
      await liveMatchApi.begin(activeCareerId);
      return seasonApi.getPayload(activeCareerId);
    });

  const onLiveMatchComplete = async () => {
    setViewedScorecard(null);
    await refresh();
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
        <View style={[styles.body, contentContainerStyle]}>
        <ScreenHeader eyebrow={`${activeCareer?.season_year ?? payload?.season ?? ''} Season`} title="Match Centre" />
        {loading && !payload && (
          <View style={styles.center}>
            <ActivityIndicator color={theme.green} />
          </View>
        )}
        {!loading && error && (
          <View style={styles.center}>
            <ThemedText themeColor="red">{error}</ThemedText>
          </View>
        )}
        {!error && payload && (
          <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
            {actionError && <ThemedText themeColor="red">{actionError}</ThemedText>}

            {payload.live_match ? (
              <LiveMatchHub
                careerId={activeCareerId}
                match={payload.live_match}
                accent={accent}
                onChange={(match) => setPayload({ ...payload, live_match: match })}
                onComplete={onLiveMatchComplete}
              />
            ) : viewedScorecard ? (
              <MatchScorecard
                card={viewedScorecard}
                onComplete={() => setViewedScorecard(null)}
                canComplete={false}
                accent={accent}
              />
            ) : payload.phase === 'draft' ? (
              <DraftHub
                careerId={activeCareerId}
                payload={payload}
                accent={accent}
                onChange={setPayload}
              />
            ) : payload.phase === 'retention' ? (
              <RetentionHub
                careerId={activeCareerId}
                payload={payload}
                accent={accent}
                onChange={setPayload}
              />
            ) : (
              <SeasonOverview
                careerId={activeCareerId}
                payload={payload}
                accent={accent}
                busy={busy}
                onChange={setPayload}
                onBeginMatch={beginMatch}
                onViewScorecard={setViewedScorecard}
              />
            )}
          </ScrollView>
        )}
        </View>
      </SafeAreaView>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Season / league_complete / playoffs / season_end overview
// ---------------------------------------------------------------------------

function SeasonOverview({
  careerId,
  payload,
  accent,
  busy,
  onChange,
  onBeginMatch,
  onViewScorecard,
}: {
  careerId: string;
  payload: LeaguePayload;
  accent?: string;
  busy: boolean;
  onChange: (payload: LeaguePayload) => void;
  onBeginMatch: () => Promise<void>;
  onViewScorecard: (card: MatchCard) => void;
}) {
  const { showError } = useError();
  const [tab, setTab] = useState<'fixtures' | 'standings' | 'recent'>('fixtures');
  const [error, setError] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState(false);

  const wrap = async (fn: () => Promise<LeaguePayload>) => {
    setBusyAction(true);
    setError(null);
    try {
      onChange(await fn());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed');
      showError(err, { onRetry: () => wrap(fn) });
    } finally {
      setBusyAction(false);
    }
  };

  const playoff = payload.playoffs[payload.playoff_index] ?? null;
  const userInPlayoff =
    payload.phase !== 'playoffs' || (playoff && [playoff.team1, playoff.team2].includes(payload.user_team ?? ''));
  const canBeginMatch = ['season', 'playoffs'].includes(payload.phase) && !payload.live_match && !!userInPlayoff;
  const canSimulate = ['season', 'playoffs'].includes(payload.phase);

  const segments: { key: typeof tab; label: string }[] = [
    { key: 'fixtures', label: payload.phase === 'playoffs' ? 'Playoffs' : 'Fixtures' },
    { key: 'standings', label: 'Standings' },
    { key: 'recent', label: 'Recent' },
  ];

  return (
    <View style={styles.overview}>
      {payload.status ? (
        <Card>
          <ThemedText style={styles.statusText}>{payload.status}</ThemedText>
          {error && (
            <ThemedText themeColor="red" style={styles.helpText}>
              {error}
            </ThemedText>
          )}
          <View style={styles.buttonRow}>
            {payload.phase === 'season_end' && (
              <Button
                label="Open Retention Window"
                variant="primary"
                accentColor={accent}
                loading={busyAction}
                onPress={() => wrap(() => seasonApi.openRetention(careerId))}
              />
            )}
            {payload.phase === 'league_complete' && (
              <Button
                label="Start Playoffs"
                variant="primary"
                accentColor={accent}
                loading={busyAction}
                onPress={() => wrap(() => seasonApi.startPlayoffs(careerId))}
              />
            )}
          </View>
        </Card>
      ) : null}

      {(canBeginMatch || canSimulate) && (
        <View style={styles.buttonRow}>
          {canBeginMatch && (
            <Button
              label={payload.phase === 'playoffs' ? 'Enter Playoff Match Hub' : 'Enter Match Hub'}
              variant="primary"
              accentColor={accent}
              loading={busy}
              onPress={onBeginMatch}
            />
          )}
          {canSimulate && (
            <Button
              label={payload.phase === 'playoffs' ? 'Quick Sim Next Playoff' : 'Quick Sim Match Day'}
              variant="secondary"
              loading={busyAction}
              onPress={() => wrap(() => seasonApi.simulateRound(careerId))}
            />
          )}
        </View>
      )}

      <SegmentedControl segments={segments} value={tab} onChange={setTab} accentColor={accent} />

      {tab === 'fixtures' &&
        (payload.phase === 'season' ? (
          <FixturesPanel payload={payload} onViewScorecard={onViewScorecard} />
        ) : payload.phase === 'league_complete' ? (
          <LeagueCompletePanel payload={payload} />
        ) : (
          <PlayoffsPanel payload={payload} />
        ))}

      {tab === 'standings' && <StandingsPanel payload={payload} accent={accent} />}

      {tab === 'recent' && <RecentMatchesPanel payload={payload} onViewScorecard={onViewScorecard} />}
    </View>
  );
}

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function FixturesPanel({
  payload,
  onViewScorecard,
}: {
  payload: LeaguePayload;
  onViewScorecard: (card: MatchCard) => void;
}) {
  const scheme = useColorScheme();
  const [week, setWeek] = useState(payload.round || 1);
  const [teamFilter, setTeamFilter] = useState('All Teams');

  // Follow the season forward after a quick-sim: `payload.round` points at the
  // NEXT (not-yet-played) round, so show the round that was just completed
  // (round - 1, clamped) — the user wants to see the fresh results, not jump
  // ahead to an empty upcoming week.
  const prevRound = useRef(payload.round);
  useEffect(() => {
    if (payload.round && payload.round !== prevRound.current) {
      const justPlayed = Math.min(Math.max(1, payload.round - 1), payload.schedule.length);
      setWeek(justPlayed);
      prevRound.current = payload.round;
    }
  }, [payload.round, payload.schedule.length]);

  const userAccent = getTeamSwatch(payload.user_team ?? '', scheme);

  const weekOptions: DropdownOption[] = useMemo(
    () => payload.schedule.map((_, i) => ({ value: String(i + 1), label: `Week ${i + 1}` })),
    [payload.schedule]
  );

  const teamOptions: DropdownOption[] = useMemo(
    () => [
      { value: 'All Teams', label: 'All Teams' },
      ...payload.teams.map((t) => ({
        value: t.name,
        label: `${t.abbr} · ${t.name}`,
        color: getTeamSwatch(t.name, scheme),
      })),
    ],
    [payload.teams, scheme]
  );

  const fixtureRows = useMemo(() => {
    if (teamFilter === 'All Teams') {
      return (payload.schedule[week - 1] || []).map((pair) => ({ week, pair }));
    }
    return payload.schedule.flatMap((roundFixtures, idx) =>
      roundFixtures.filter((pair) => pair.includes(teamFilter)).map((pair) => ({ week: idx + 1, pair }))
    );
  }, [payload.schedule, week, teamFilter]);

  return (
    <View style={styles.panelGap}>
      <View style={styles.filterRow}>
        <Dropdown
          label="Week"
          value={String(week)}
          options={weekOptions}
          onChange={(v) => setWeek(Number(v))}
          accentColor={userAccent}
          style={styles.filterControl}
        />
        <Dropdown
          label="Team"
          value={teamFilter}
          options={teamOptions}
          onChange={setTeamFilter}
          accentColor={userAccent}
          style={styles.filterControl}
        />
      </View>
      {fixtureRows.map(({ week: w, pair }, i) => (
        <FixtureCard key={i} payload={payload} week={w} pair={pair} onViewScorecard={onViewScorecard} />
      ))}
      {fixtureRows.length === 0 && (
        <ThemedText themeColor="textDim" style={styles.helpText}>
          No fixtures found.
        </ThemedText>
      )}
    </View>
  );
}

function FixtureCard({
  payload,
  week,
  pair,
  onViewScorecard,
}: {
  payload: LeaguePayload;
  week: number;
  pair: ScheduleFixture;
  onViewScorecard: (card: MatchCard) => void;
}) {
  const [a, b] = pair;
  const ta = payload.teams.find((t) => t.name === a);
  const tb = payload.teams.find((t) => t.name === b);
  const result = (payload.fixture_results || []).find(
    (c) => c.round === week && ((c.team1 === a && c.team2 === b) || (c.team1 === b && c.team2 === a))
  );

  if (result) {
    const winnerColor = TeamColors[result.winner]?.primary;
    return (
      <Pressable onPress={() => onViewScorecard(result)}>
        <Card style={[styles.fixtureCard, { borderLeftWidth: 3, borderLeftColor: winnerColor ?? 'transparent' }]}>
          <Pill label={`Week ${week}`} />
          <ThemedText style={styles.fixtureTitle}>
            {teamAbbr(result.winner)} {result.margin}
          </ThemedText>
          <ThemedText themeColor="textDim" style={styles.fixtureSub}>
            {a} vs {b}
          </ThemedText>
          <ThemedText themeColor="textFaint" style={styles.fixtureSub}>
            {result.innings.map((inn) => `${teamAbbr(inn.team)} ${inn.score}`).join(' · ')} · 🏆 {result.motm}
          </ThemedText>
        </Card>
      </Pressable>
    );
  }

  return (
    <Card style={styles.fixtureCard}>
      <Pill label={`Week ${week}`} />
      <ThemedText style={styles.fixtureTitle}>
        {teamAbbr(a)} vs {teamAbbr(b)}
      </ThemedText>
      <ThemedText themeColor="textDim" style={styles.fixtureSub}>
        {a} vs {b}
      </ThemedText>
      <ThemedText themeColor="textFaint" style={styles.fixtureSub}>
        {ta?.abbr ?? a} {ta?.wins ?? 0}-{ta?.losses ?? 0} vs {tb?.abbr ?? b} {tb?.wins ?? 0}-{tb?.losses ?? 0} ·{' '}
        {ta?.home ?? 'Cricket Stadium'}
      </ThemedText>
    </Card>
  );
}

function LeagueCompletePanel({ payload }: { payload: LeaguePayload }) {
  return (
    <View style={styles.panelGap}>
      <ThemedText themeColor="textDim" style={styles.helpText}>
        Regular season is complete. The table and stats are frozen until you start playoffs.
      </ThemedText>
      {payload.standings.slice(0, 4).map((t, i) => (
        <Card key={t.name} style={styles.fixtureCard}>
          <Pill label={`Seed ${i + 1}`} accentColor={t.primary} secondaryColor={t.accent} />
          <ThemedText style={styles.fixtureTitle}>
            {teamAbbr(t.name)} · {t.name}
          </ThemedText>
          <ThemedText themeColor="textDim" style={styles.fixtureSub}>
            {t.wins}-{t.losses} · {t.points} pts · NRR {t.nrr.toFixed(3)}
          </ThemedText>
        </Card>
      ))}
    </View>
  );
}

function PlayoffsPanel({ payload }: { payload: LeaguePayload }) {
  return (
    <View style={styles.panelGap}>
      {payload.playoffs.map((p, i) => (
        <PlayoffCard key={i} match={p} />
      ))}
      {payload.playoffs.length === 0 && (
        <ThemedText themeColor="textDim" style={styles.helpText}>
          Playoffs appear after 14 league matches.
        </ThemedText>
      )}
    </View>
  );
}

/** A single playoff bracket card, with extra gold styling for the Final. */
function PlayoffCard({ match: p }: { match: PlayoffMatch }) {
  const scheme = useColorScheme();
  const isFinal = p.name === 'Final';
  return (
    <Card
      style={[
        styles.fixtureCard,
        isFinal && styles.finalCard,
        isFinal && { borderColor: GOLD, backgroundColor: scheme === 'dark' ? '#2a2310' : '#fffbe9' },
      ]}>
      <Pill label={p.status} accentColor={isFinal ? GOLD : undefined} />
      <ThemedText style={[styles.fixtureTitle, isFinal && { color: GOLD }]}>
        {isFinal ? '🏆 ' : ''}
        {p.name}
      </ThemedText>
      <ThemedText themeColor="textDim" style={styles.fixtureSub}>
        {p.team1 ? teamAbbr(p.team1) : 'TBD'} vs {p.team2 ? teamAbbr(p.team2) : 'TBD'}
      </ThemedText>
      {p.winner && (
        <ThemedText style={[styles.fixtureResultLine, isFinal && { color: GOLD }]}>
          {teamAbbr(p.winner)} {isFinal ? 'are champions!' : 'advanced'}
        </ThemedText>
      )}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Standings
// ---------------------------------------------------------------------------

function StandingsPanel({ payload, accent }: { payload: LeaguePayload; accent?: string }) {
  const theme = useTheme();
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <View style={styles.panelGap}>
      <Card style={styles.standingsCard}>
        <View style={styles.standingsHeaderRow}>
          <ThemedText themeColor="textFaint" style={[styles.standingsHeaderCell, styles.posCol]}>
            #
          </ThemedText>
          <ThemedText themeColor="textFaint" style={[styles.standingsHeaderCell, styles.teamCol]}>
            Team
          </ThemedText>
          <ThemedText themeColor="textFaint" style={styles.standingsHeaderCell}>
            P
          </ThemedText>
          <ThemedText themeColor="textFaint" style={styles.standingsHeaderCell}>
            W
          </ThemedText>
          <ThemedText themeColor="textFaint" style={styles.standingsHeaderCell}>
            L
          </ThemedText>
          <ThemedText themeColor="textFaint" style={styles.standingsHeaderCell}>
            Pts
          </ThemedText>
          <ThemedText themeColor="textFaint" style={styles.standingsHeaderCell}>
            NRR
          </ThemedText>
        </View>
        {payload.standings.map((t, i) => {
          const isOpen = expanded === t.name;
          const topRuns = [...t.roster].sort((a, b) => b.runs - a.runs).slice(0, 3);
          const topWkts = [...t.roster].sort((a, b) => b.wickets - a.wickets).slice(0, 3);
          const mvp = [...t.roster].sort((a, b) => b.mvp - a.mvp)[0];
          return (
            <View key={t.name}>
              <Pressable
                onPress={() => setExpanded(isOpen ? null : t.name)}
                style={[styles.standingsRow, { borderBottomColor: theme.border }]}>
                <ThemedText style={[styles.standingsCell, styles.posCol]}>{i + 1}</ThemedText>
                <View style={styles.teamCol}>
                  <ThemedText style={[styles.standingsTeam, t.name === payload.user_team && { color: accent ?? theme.green }]} numberOfLines={1}>
                    {t.abbr}
                  </ThemedText>
                </View>
                <ThemedText style={styles.standingsCell}>{t.played}</ThemedText>
                <ThemedText style={styles.standingsCell}>{t.wins}</ThemedText>
                <ThemedText style={styles.standingsCell}>{t.losses}</ThemedText>
                <ThemedText style={styles.standingsCell}>{t.points}</ThemedText>
                <ThemedText style={styles.standingsCell}>{t.nrr.toFixed(3)}</ThemedText>
              </Pressable>
              {isOpen && (
                <View style={[styles.teamDrop, { borderColor: theme.border }]}>
                  <ThemedText themeColor="textDim" style={styles.teamDropLine}>
                    Captain: {t.captain || '-'} · MVP: {mvp?.name || '-'} ({mvp?.mvp ?? 0})
                  </ThemedText>
                  <ThemedText themeColor="textDim" style={styles.teamDropLine}>
                    Top runs: {topRuns.map((p) => `${p.name} ${p.runs}`).join(', ') || '-'}
                  </ThemedText>
                  <ThemedText themeColor="textDim" style={styles.teamDropLine}>
                    Top wickets: {topWkts.map((p) => `${p.name} ${p.wickets}`).join(', ') || '-'}
                  </ThemedText>
                </View>
              )}
            </View>
          );
        })}
      </Card>

      {payload.playoffs.length > 0 && (
        <View style={styles.panelGap}>
          <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
            Playoffs
          </ThemedText>
          {payload.playoffs.map((p, i) => (
            <Card key={i} style={styles.fixtureCard}>
              <Pill label={p.status} />
              <ThemedText style={styles.fixtureTitle}>{p.name}</ThemedText>
              <ThemedText themeColor="textDim" style={styles.fixtureSub}>
                {p.team1 || 'TBD'} vs {p.team2 || 'TBD'}
              </ThemedText>
              {p.winner && <ThemedText style={styles.fixtureResultLine}>{p.winner} advanced</ThemedText>}
            </Card>
          ))}
        </View>
      )}
    </View>
  );
}

// ---------------------------------------------------------------------------
// Recent matches
// ---------------------------------------------------------------------------

function RecentMatchesPanel({
  payload,
  onViewScorecard,
}: {
  payload: LeaguePayload;
  onViewScorecard: (card: MatchCard) => void;
}) {
  const matches = [...payload.match_log].reverse();
  if (matches.length === 0) {
    return (
      <ThemedText themeColor="textDim" style={styles.helpText}>
        No matches played yet.
      </ThemedText>
    );
  }
  return (
    <View style={styles.panelGap}>
      {matches.map((card, i) => (
        <Pressable key={i} onPress={() => onViewScorecard(card)}>
          <Card style={[styles.fixtureCard, { borderLeftWidth: 3, borderLeftColor: TeamColors[card.winner]?.primary ?? 'transparent' }]}>
            <Pill label={card.stage} />
            <ThemedText style={styles.fixtureTitle}>
              {teamAbbr(card.winner)} {card.margin}
            </ThemedText>
            <ThemedText themeColor="textDim" style={styles.fixtureSub}>
              {card.venue} · Toss: {card.toss} · 🏆 MOTM: {card.motm}
            </ThemedText>
            <ThemedText themeColor="textFaint" style={styles.fixtureSub}>
              {card.innings.map((inn) => `${teamAbbr(inn.team)} ${inn.score}`).join(' · ')}
            </ThemedText>
          </Card>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  body: {
    flex: 1,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    padding: Spacing.three,
    gap: Spacing.three,
    paddingBottom: ContentBottomInset,
  },
  overview: {
    gap: Spacing.three,
  },
  statusText: {
    fontSize: 13.5,
    lineHeight: 19,
    fontWeight: '600',
    marginBottom: Spacing.two,
  },
  helpText: {
    fontSize: 12.5,
    lineHeight: 18,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: Spacing.two,
  },
  panelGap: {
    gap: Spacing.two,
  },
  pillRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  filterRow: {
    flexDirection: 'row',
    gap: Spacing.two,
    marginBottom: Spacing.one,
  },
  filterControl: {
    flex: 1,
  },
  fixtureCard: {
    gap: 4,
  },
  finalCard: {
    borderWidth: 2,
  },
  fixtureTitle: {
    fontSize: 14.5,
    fontWeight: '800',
  },
  fixtureSub: {
    fontSize: 11.5,
  },
  fixtureResultLine: {
    fontSize: 12.5,
    fontWeight: '700',
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  standingsCard: {
    paddingHorizontal: Spacing.two,
    paddingVertical: Spacing.two,
  },
  standingsHeaderRow: {
    flexDirection: 'row',
    paddingBottom: 6,
    paddingHorizontal: Spacing.one,
  },
  standingsHeaderCell: {
    flex: 1,
    fontSize: 10,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    textAlign: 'right',
  },
  standingsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: Spacing.one,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  standingsCell: {
    flex: 1,
    fontSize: 12.5,
    textAlign: 'right',
  },
  posCol: {
    flex: 0.6,
    textAlign: 'left',
  },
  teamCol: {
    flex: 1.4,
  },
  standingsTeam: {
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 0.4,
  },
  teamDrop: {
    borderWidth: 1,
    borderRadius: 8,
    padding: Spacing.two,
    marginBottom: Spacing.two,
    gap: 2,
  },
  teamDropLine: {
    fontSize: 11.5,
    lineHeight: 16,
  },
});
