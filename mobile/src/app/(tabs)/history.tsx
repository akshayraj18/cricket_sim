import { useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { MatchCard, PlayerDict, SeasonHistoryEntry } from '@/api/types';
import { NoActiveCareer } from '@/components/empty-state';
import { MatchScorecard } from '@/components/match-scorecard';
import { PlayerProfileSheet } from '@/components/player-profile-sheet';
import { ScreenHeader } from '@/components/screen-header';
import { ThemedText } from '@/components/themed-text';
import { Card } from '@/components/ui/card';
import { Pill } from '@/components/ui/pill';
import { SegmentedControl } from '@/components/ui/segmented-control';
import { ContentBottomInset, getLegibleAccentValue, GOLD, Radius, Spacing, TeamColors, teamAbbr } from '@/constants/theme';
import { useCareer } from '@/context/CareerContext';
import { useLeague } from '@/context/LeagueContext';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { useTheme } from '@/hooks/use-theme';

type HistoryTab = 'log' | 'seasons' | 'alltime';

const TABS: { key: HistoryTab; label: string }[] = [
  { key: 'log', label: 'Match Log' },
  { key: 'seasons', label: 'Past Seasons' },
  { key: 'alltime', label: 'All-Time' },
];

/** Aggregates a counting stat (e.g. runs, wickets) for `name` across every season's archived top performers. */
function sumAcrossSeasons(
  seasonHistory: SeasonHistoryEntry[],
  currentTables: { batting: PlayerDict[]; bowling: PlayerDict[] } | undefined,
  list: 'batting' | 'bowling',
  statKey: keyof PlayerDict
): { name: string; team: string; total: number }[] {
  const totals = new Map<string, { name: string; team: string; total: number }>();
  const add = (rows: PlayerDict[] | undefined) => {
    for (const p of rows ?? []) {
      const value = Number(p[statKey] ?? 0) || 0;
      if (!value) continue;
      const existing = totals.get(p.name);
      if (existing) {
        existing.total += value;
        existing.team = p.team || existing.team;
      } else {
        totals.set(p.name, { name: p.name, team: p.team || '', total: value });
      }
    }
  };
  for (const season of seasonHistory) add(season[list]);
  add(currentTables?.[list]);
  return [...totals.values()].sort((a, b) => b.total - a.total);
}

/**
 * Aggregates a counting stat (e.g. sixes, catches) for `name` across every season's full
 * award-race leaderboard for `listKey`, plus the current season's live leaderboard.
 * Falls back to `legacyList` (`batting`/`bowling`, top-15-only) for seasons archived before
 * `leaderboards` was stored.
 */
function sumLeaderboardAcrossSeasons(
  seasonHistory: SeasonHistoryEntry[],
  currentLeaderboards: Record<string, PlayerDict[]> | undefined,
  listKey: string,
  statKey: keyof PlayerDict,
  legacyList?: 'batting' | 'bowling'
): { name: string; team: string; total: number }[] {
  const totals = new Map<string, { name: string; team: string; total: number }>();
  const add = (rows: PlayerDict[] | undefined) => {
    for (const p of rows ?? []) {
      const value = Number(p[statKey] ?? 0) || 0;
      if (!value) continue;
      const existing = totals.get(p.name);
      if (existing) {
        existing.total += value;
        existing.team = p.team || existing.team;
      } else {
        totals.set(p.name, { name: p.name, team: p.team || '', total: value });
      }
    }
  };
  for (const season of seasonHistory) {
    if (season.leaderboards) add(season.leaderboards[listKey]);
    else if (legacyList) add(season[legacyList]);
  }
  add(currentLeaderboards?.[listKey]);
  return [...totals.values()].sort((a, b) => b.total - a.total);
}

/**
 * Finds the single best-ever performance for `name` across seasons — e.g. career-highest score
 * or career-best bowling figures — by taking, per player, whichever season's entry in `listKey`
 * compares highest under `better`. `formatValue`/`formatContext` render the display value and
 * the "vs OPPONENT" context for that best performance.
 */
function bestAcrossSeasons(
  seasonHistory: SeasonHistoryEntry[],
  currentLeaderboards: Record<string, PlayerDict[]> | undefined,
  listKey: string,
  better: (a: PlayerDict, b: PlayerDict) => boolean,
  formatValue: (p: PlayerDict) => string,
  formatContext: (p: PlayerDict) => string
): { name: string; team: string; total: string; context: string }[] {
  const best = new Map<string, PlayerDict>();
  const consider = (rows: PlayerDict[] | undefined) => {
    for (const p of rows ?? []) {
      const existing = best.get(p.name);
      if (!existing || better(p, existing)) best.set(p.name, p);
    }
  };
  for (const season of seasonHistory) {
    if (season.leaderboards) consider(season.leaderboards[listKey]);
  }
  consider(currentLeaderboards?.[listKey]);
  return [...best.values()]
    .sort((a, b) => (better(a, b) ? -1 : better(b, a) ? 1 : 0))
    .map((p) => ({ name: p.name, team: p.team || '', total: formatValue(p), context: formatContext(p) }));
}

/**
 * Computes a career rate stat (strike rate or economy) for `name` from totals summed across
 * seasons — e.g. career SR = total runs / total balls faced * 100. `numKey`/`denKey` are the
 * counting fields to sum from each season's `listKey` leaderboard (which includes every player
 * who recorded the underlying activity, not just rate-qualified ones).
 */
function careerRateAcrossSeasons(
  seasonHistory: SeasonHistoryEntry[],
  currentLeaderboards: Record<string, PlayerDict[]> | undefined,
  listKey: string,
  numKey: keyof PlayerDict,
  denKey: keyof PlayerDict,
  minDen: number,
  rate: (num: number, den: number) => number
): { name: string; team: string; total: number }[] {
  const sums = new Map<string, { name: string; team: string; num: number; den: number }>();
  const add = (rows: PlayerDict[] | undefined) => {
    for (const p of rows ?? []) {
      const num = Number(p[numKey] ?? 0) || 0;
      const den = Number(p[denKey] ?? 0) || 0;
      if (!den) continue;
      const existing = sums.get(p.name);
      if (existing) {
        existing.num += num;
        existing.den += den;
        existing.team = p.team || existing.team;
      } else {
        sums.set(p.name, { name: p.name, team: p.team || '', num, den });
      }
    }
  };
  for (const season of seasonHistory) {
    if (season.leaderboards) add(season.leaderboards[listKey]);
  }
  add(currentLeaderboards?.[listKey]);
  return [...sums.values()]
    .filter((s) => s.den >= minDen)
    .map((s) => ({ name: s.name, team: s.team, total: rate(s.num, s.den) }));
}

/** Counts how many times each player has won a season MVP or Final, across `seasonHistory`. */
function countAwards(
  seasonHistory: SeasonHistoryEntry[],
  pick: (entry: SeasonHistoryEntry) => { name: string; team: string } | null
): { name: string; team: string; total: number }[] {
  const totals = new Map<string, { name: string; team: string; total: number }>();
  for (const entry of seasonHistory) {
    const winner = pick(entry);
    if (!winner?.name) continue;
    const existing = totals.get(winner.name);
    if (existing) existing.total += 1;
    else totals.set(winner.name, { name: winner.name, team: winner.team, total: 1 });
  }
  return [...totals.values()].sort((a, b) => b.total - a.total);
}

/** Parses a "W/R" bowling-figures label (e.g. "4/22") into `[wickets, runs]`, or `[0, 999]` for "-". */
function parseBestBowling(label: string | undefined): [number, number] {
  if (!label || label === '-') return [0, 999];
  const [wkts, runs] = label.split('/').map(Number);
  return [wkts || 0, runs || 0];
}

export default function HistoryScreen() {
  const theme = useTheme();
  const { activeCareerId, activeCareer } = useCareer();
  const { payload, loading, error } = useLeague();
  const [tab, setTab] = useState<HistoryTab>('log');
  const [viewedScorecard, setViewedScorecard] = useState<MatchCard | null>(null);

  const team = useMemo(
    () => payload?.teams.find((t) => t.name === payload.user_team),
    [payload]
  );
  const accent = team?.accent;

  const matchLog = useMemo(() => [...(payload?.match_log ?? [])].reverse(), [payload]);
  const seasonHistory = useMemo(() => [...(payload?.history ?? [])].reverse(), [payload]);

  const [profilePlayer, setProfilePlayer] = useState<PlayerDict | null>(null);

  const allTimeOrangeCap = useMemo(
    () => sumAcrossSeasons(payload?.history ?? [], payload?.tables, 'batting', 'runs'),
    [payload]
  );
  const allTimePurpleCap = useMemo(
    () => sumAcrossSeasons(payload?.history ?? [], payload?.tables, 'bowling', 'wickets'),
    [payload]
  );
  const allTimeMvps = useMemo(
    () =>
      countAwards(payload?.history ?? [], (entry) =>
        entry.mvp ? { name: entry.mvp.name, team: entry.mvp.team } : null
      ),
    [payload]
  );
  const allTimeTitles = useMemo(
    () =>
      countAwards(payload?.history ?? [], (entry) =>
        entry.champion ? { name: entry.champion, team: entry.champion } : null
      ),
    [payload]
  );
  const allTimeMvpRace = useMemo(
    () => sumLeaderboardAcrossSeasons(payload?.history ?? [], payload?.leaderboards, 'mvp', 'mvp'),
    [payload]
  );
  const allTimeSixes = useMemo(
    () => sumLeaderboardAcrossSeasons(payload?.history ?? [], payload?.leaderboards, 'sixes', 'sixes', 'batting'),
    [payload]
  );
  const allTimeFours = useMemo(
    () => sumLeaderboardAcrossSeasons(payload?.history ?? [], payload?.leaderboards, 'fours', 'fours', 'batting'),
    [payload]
  );
  const allTimeBoundaries = useMemo(
    () => sumLeaderboardAcrossSeasons(payload?.history ?? [], payload?.leaderboards, 'boundaries', 'boundaries'),
    [payload]
  );
  const allTimeCatches = useMemo(
    () => sumLeaderboardAcrossSeasons(payload?.history ?? [], payload?.leaderboards, 'catches', 'catches'),
    [payload]
  );
  const allTimeStumpings = useMemo(
    () => sumLeaderboardAcrossSeasons(payload?.history ?? [], payload?.leaderboards, 'stumpings', 'stumpings'),
    [payload]
  );
  const allTimeRunouts = useMemo(
    () => sumLeaderboardAcrossSeasons(payload?.history ?? [], payload?.leaderboards, 'runouts', 'runouts'),
    [payload]
  );
  const allTimeHighestScore = useMemo(
    () =>
      bestAcrossSeasons(
        payload?.history ?? [],
        payload?.leaderboards,
        'highest_score',
        (a, b) => a.hs > b.hs,
        (p) => `${p.hs}`,
        (p) => (p.hs_against ? `vs ${p.hs_against}` : '')
      ),
    [payload]
  );
  const allTimeBestBowling = useMemo(
    () =>
      bestAcrossSeasons(
        payload?.history ?? [],
        payload?.leaderboards,
        'best_figures',
        (a, b) => {
          const [aw, ar] = parseBestBowling(a.best_bowling);
          const [bw, br] = parseBestBowling(b.best_bowling);
          return aw !== bw ? aw > bw : ar < br;
        },
        (p) => p.best_bowling,
        (p) => (p.best_bowling_against ? `vs ${p.best_bowling_against}` : '')
      ),
    [payload]
  );
  const allTimeStrikeRate = useMemo(
    () =>
      careerRateAcrossSeasons(
        payload?.history ?? [],
        payload?.leaderboards,
        'orange_cap',
        'runs',
        'balls',
        30,
        (runs, balls) => Math.round((runs / balls) * 10000) / 100
      ),
    [payload]
  );
  const allTimeEconomy = useMemo(
    () =>
      careerRateAcrossSeasons(
        payload?.history ?? [],
        payload?.leaderboards,
        'purple_cap',
        'runs_conceded',
        'balls_bowled',
        18,
        (runsConceded, balls) => Math.round((runsConceded / (balls / 6)) * 100) / 100
      ).sort((a, b) => a.total - b.total),
    [payload]
  );

  const allPlayersByName = useMemo(() => {
    const map = new Map<string, PlayerDict>();
    for (const t of payload?.teams ?? []) {
      for (const p of t.roster) map.set(p.name, p);
    }
    return map;
  }, [payload]);

  const openProfile = (name: string) => {
    const p = allPlayersByName.get(name);
    if (p) setProfilePlayer(p);
  };

  if (!activeCareerId) {
    return (
      <View style={[styles.container, { backgroundColor: theme.bg }]}>
        <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
          <ScreenHeader title="League History" />
          <NoActiveCareer />
        </SafeAreaView>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
        <ScreenHeader eyebrow={activeCareer?.name} title="League History" />
        {loading && (
          <View style={styles.center}>
            <ActivityIndicator color={theme.green} />
          </View>
        )}
        {!loading && error && (
          <View style={styles.center}>
            <ThemedText themeColor="red">{error}</ThemedText>
          </View>
        )}
        {!loading && !error && payload && (
          <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
            {viewedScorecard ? (
              <MatchScorecard
                card={viewedScorecard}
                onComplete={() => setViewedScorecard(null)}
                canComplete={false}
                accent={accent}
              />
            ) : (
              <>
                <SegmentedControl segments={TABS} value={tab} onChange={setTab} accentColor={accent} />

                {tab === 'log' && (
                  <ScrollView
                    style={styles.logScroll}
                    contentContainerStyle={styles.list}
                    nestedScrollEnabled
                    showsVerticalScrollIndicator={false}>
                    {matchLog.map((card, i) => (
                      <MatchLogRow key={i} card={card} accent={accent} onPress={() => setViewedScorecard(card)} />
                    ))}
                    {matchLog.length === 0 && (
                      <ThemedText themeColor="textDim" style={styles.helpText}>
                        No matches played yet this season.
                      </ThemedText>
                    )}
                  </ScrollView>
                )}

                {tab === 'seasons' && (
                  <ScrollView
                    style={styles.logScroll}
                    contentContainerStyle={styles.list}
                    nestedScrollEnabled
                    showsVerticalScrollIndicator={false}>
                    {seasonHistory.map((entry) => (
                      <SeasonHistoryCard key={entry.season} entry={entry} accent={accent} userTeam={payload.user_team} />
                    ))}
                    {seasonHistory.length === 0 && (
                      <ThemedText themeColor="textDim" style={styles.helpText}>
                        Finish a season to build league history. Champions, runners-up, MVPs, and final tables will
                        appear here.
                      </ThemedText>
                    )}
                  </ScrollView>
                )}

                {tab === 'alltime' && (
                  <View style={styles.leaderGrid}>
                    <AllTimeLeaderCard
                      title="Orange Cap (All-Time)"
                      rows={allTimeOrangeCap}
                      suffix="runs"
                      color="#f97316"
                      onPlayerPress={openProfile}
                    />
                    <AllTimeLeaderCard
                      title="MVP Race (All-Time)"
                      rows={allTimeMvpRace}
                      suffix="pts"
                      color="#0f172a"
                      onPlayerPress={openProfile}
                    />
                    <AllTimeLeaderCard
                      title="Most Sixes (All-Time)"
                      rows={allTimeSixes}
                      suffix="6s"
                      color="#dc2626"
                      onPlayerPress={openProfile}
                    />
                    <AllTimeLeaderCard
                      title="Most Fours (All-Time)"
                      rows={allTimeFours}
                      suffix="4s"
                      color="#2563eb"
                      onPlayerPress={openProfile}
                    />
                    <AllTimeLeaderCard
                      title="Most Boundaries (All-Time)"
                      rows={allTimeBoundaries}
                      suffix="boundaries"
                      color="#059669"
                      onPlayerPress={openProfile}
                    />
                    <AllTimeLeaderCard
                      title="Highest Score (All-Time)"
                      rows={allTimeHighestScore}
                      color="#b45309"
                      onPlayerPress={openProfile}
                    />
                    <AllTimeLeaderCard
                      title="Best Strike Rate (All-Time)"
                      rows={allTimeStrikeRate}
                      color="#db2777"
                      onPlayerPress={openProfile}
                    />
                    <AllTimeLeaderCard
                      title="Purple Cap (All-Time)"
                      rows={allTimePurpleCap}
                      suffix="wkts"
                      color="#7c3aed"
                      onPlayerPress={openProfile}
                    />
                    <AllTimeLeaderCard
                      title="Best Economy (All-Time)"
                      rows={allTimeEconomy}
                      color="#0891b2"
                      onPlayerPress={openProfile}
                    />
                    <AllTimeLeaderCard
                      title="Best Bowling (All-Time)"
                      rows={allTimeBestBowling}
                      color="#6d28d9"
                      onPlayerPress={openProfile}
                    />
                    <AllTimeLeaderCard
                      title="Most Catches (All-Time)"
                      rows={allTimeCatches}
                      suffix="ct"
                      color="#16a34a"
                      onPlayerPress={openProfile}
                    />
                    <AllTimeLeaderCard
                      title="Most Stumpings (All-Time)"
                      rows={allTimeStumpings}
                      suffix="st"
                      color="#0d9488"
                      onPlayerPress={openProfile}
                    />
                    <AllTimeLeaderCard
                      title="Most Run Outs (All-Time)"
                      rows={allTimeRunouts}
                      suffix="ro"
                      color="#ca8a04"
                      onPlayerPress={openProfile}
                    />
                    <AllTimeLeaderCard
                      title="Most MVP Awards"
                      rows={allTimeMvps}
                      suffix="awards"
                      color={GOLD}
                      onPlayerPress={openProfile}
                    />
                    <AllTimeLeaderCard
                      title="Most Titles"
                      rows={allTimeTitles}
                      suffix="titles"
                      color={GOLD}
                      isTeam
                    />
                    {seasonHistory.length === 0 && (
                      <ThemedText themeColor="textDim" style={styles.helpText}>
                        Finish a season to start tracking all-time leaderboards, MVPs, and titles.
                      </ThemedText>
                    )}
                  </View>
                )}
              </>
            )}
          </ScrollView>
        )}
        <PlayerProfileSheet player={profilePlayer} onClose={() => setProfilePlayer(null)} accentColor={accent} />
      </SafeAreaView>
    </View>
  );
}

function AllTimeLeaderCard({
  title,
  rows,
  suffix,
  color,
  onPlayerPress,
  isTeam,
}: {
  title: string;
  rows: { name: string; team: string; total: number | string; context?: string }[];
  suffix?: string;
  color: string;
  onPlayerPress?: (name: string) => void;
  /** When true, `name`/`team` refer to a franchise rather than a player (used for "Most Titles"). */
  isTeam?: boolean;
}) {
  const theme = useTheme();
  const scheme = useColorScheme();
  // Keep the value text legible in dark mode (near-black accents like MVP's
  // slate would vanish), while the stripe keeps the vivid color.
  const valueColor = getLegibleAccentValue(color, scheme);
  return (
    <Card style={styles.leaderCard}>
      <View style={[styles.leaderAccent, { backgroundColor: color }]} />
      <ThemedText style={styles.leaderTitle}>{title}</ThemedText>
      <ScrollView style={styles.allTimeList} nestedScrollEnabled showsVerticalScrollIndicator={false}>
        {rows.map((row, i) => {
          const sub = row.context ? [row.team, row.context].filter(Boolean).join(' · ') : row.team;
          const content = (
            <>
              <ThemedText themeColor="textFaint" style={styles.leaderRank}>
                {i + 1}
              </ThemedText>
              <View style={styles.flex1}>
                <ThemedText style={styles.leaderName} numberOfLines={1}>
                  {isTeam ? teamAbbr(row.name) : row.name}
                </ThemedText>
                {!isTeam && sub ? (
                  <ThemedText themeColor="textFaint" style={styles.leaderTeam} numberOfLines={1}>
                    {sub}
                  </ThemedText>
                ) : null}
              </View>
              <ThemedText style={[styles.leaderValue, { color: valueColor }]}>
                {typeof row.total === 'number' && !Number.isInteger(row.total)
                  ? Math.round(row.total * 10) / 10
                  : row.total}
                {suffix ? ` ${suffix}` : ''}
              </ThemedText>
            </>
          );
          if (onPlayerPress) {
            return (
              <Pressable
                key={row.name}
                onPress={() => onPlayerPress(row.name)}
                style={[styles.leaderRow, { borderBottomColor: theme.border }]}>
                {content}
              </Pressable>
            );
          }
          return (
            <View key={row.name} style={[styles.leaderRow, { borderBottomColor: theme.border }]}>
              {content}
            </View>
          );
        })}
        {rows.length === 0 && (
          <ThemedText themeColor="textDim" style={styles.emptyText}>
            No data yet.
          </ThemedText>
        )}
      </ScrollView>
    </Card>
  );
}

function MatchLogRow({ card, accent, onPress }: { card: MatchCard; accent?: string; onPress: () => void }) {
  const theme = useTheme();
  const winnerColor = TeamColors[card.winner]?.primary ?? accent ?? theme.green;
  return (
    <Pressable onPress={onPress}>
      <Card style={[styles.logCard, { borderLeftWidth: 3, borderLeftColor: winnerColor }]}>
        <View style={styles.logHeaderRow}>
          <Pill label={card.stage === 'league' ? `Week ${card.round}` : card.stage} />
          {card.motm ? <Pill label={`MOTM: ${card.motm}`} accentColor={accent} /> : null}
        </View>
        <ThemedText style={styles.logTitle}>
          {teamAbbr(card.team1)} vs {teamAbbr(card.team2)}
        </ThemedText>
        <ThemedText themeColor="textDim" style={styles.logSub} numberOfLines={1}>
          {card.venue ? `${card.venue} · ` : ''}
          {card.toss}
        </ThemedText>
        <ThemedText style={[styles.logResult, { color: winnerColor }]} numberOfLines={1}>
          {teamAbbr(card.winner)} {card.margin}
        </ThemedText>
        {card.innings.map((inn, i) => (
          <ThemedText key={i} themeColor="textDim" style={styles.logScore}>
            {teamAbbr(inn.team)} {inn.score}
          </ThemedText>
        ))}
      </Card>
    </Pressable>
  );
}

function SeasonHistoryCard({
  entry,
  accent,
  userTeam,
}: {
  entry: SeasonHistoryEntry;
  accent?: string;
  userTeam: string | null;
}) {
  const theme = useTheme();
  return (
    <Card style={styles.seasonCard}>
      <ThemedText style={styles.seasonTitle}>Season {entry.season}</ThemedText>
      <View style={styles.seasonResultRow}>
        <View style={styles.flex1}>
          <ThemedText themeColor="textFaint" style={styles.seasonLabel}>
            Champion
          </ThemedText>
          <ThemedText style={[styles.seasonValue, { color: theme.green }]} numberOfLines={1}>
            {teamAbbr(entry.champion)} · {entry.champion}
          </ThemedText>
        </View>
        <View style={styles.flex1}>
          <ThemedText themeColor="textFaint" style={styles.seasonLabel}>
            Runner-up
          </ThemedText>
          <ThemedText style={styles.seasonValue} numberOfLines={1}>
            {teamAbbr(entry.runner_up)} · {entry.runner_up}
          </ThemedText>
        </View>
      </View>
      {entry.mvp ? (
        <View style={styles.seasonResultRow}>
          <View style={styles.flex1}>
            <ThemedText themeColor="textFaint" style={styles.seasonLabel}>
              MVP
            </ThemedText>
            <ThemedText style={styles.seasonValue} numberOfLines={1}>
              {entry.mvp.name} ({teamAbbr(entry.mvp.team)}) · {entry.mvp.mvp} pts
            </ThemedText>
          </View>
        </View>
      ) : null}

      {entry.playoffs?.length ? (
        <View style={styles.playoffList}>
          {entry.playoffs.map((p, i) => {
            const isFinal = p.name === 'Final';
            return (
              <View
                key={i}
                style={[
                  styles.playoffRow,
                  { borderBottomColor: theme.border },
                  isFinal && { borderBottomWidth: 0 },
                ]}>
                <ThemedText
                  themeColor={isFinal ? undefined : 'textFaint'}
                  style={[styles.playoffStage, isFinal && { color: GOLD }]}>
                  {isFinal ? '🏆 ' : ''}
                  {p.name}
                </ThemedText>
                <ThemedText style={[styles.playoffResult, isFinal && { color: GOLD }]} numberOfLines={1}>
                  {teamAbbr(p.winner)} bt {teamAbbr(p.loser)}
                </ThemedText>
              </View>
            );
          })}
        </View>
      ) : null}

      <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
        Final Table
      </ThemedText>
      <View style={[styles.tableHeaderRow, { borderBottomColor: theme.border }]}>
        <ThemedText themeColor="textFaint" style={[styles.cell, styles.posCol]}>
          #
        </ThemedText>
        <ThemedText themeColor="textFaint" style={[styles.cell, styles.teamCol]}>
          Team
        </ThemedText>
        <ThemedText themeColor="textFaint" style={[styles.cell, styles.numCol]}>
          Pts
        </ThemedText>
        <ThemedText themeColor="textFaint" style={[styles.cell, styles.numCol]}>
          NRR
        </ThemedText>
      </View>
      {entry.points_table.map((t, i) => (
        <View
          key={t.name}
          style={[
            styles.tableRow,
            { borderBottomColor: theme.border },
            t.name === userTeam && { backgroundColor: theme.bgElevated },
          ]}>
          <ThemedText style={[styles.cell, styles.posCol]}>{i + 1}</ThemedText>
          <ThemedText style={[styles.cell, styles.teamCol, styles.teamName]} numberOfLines={1}>
            {teamAbbr(t.name)}
          </ThemedText>
          <ThemedText style={[styles.cell, styles.numCol]}>{t.points}</ThemedText>
          <ThemedText style={[styles.cell, styles.numCol]}>{Number(t.nrr).toFixed(3)}</ThemedText>
        </View>
      ))}
    </Card>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
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
  helpText: {
    fontSize: 12.5,
    lineHeight: 18,
  },
  list: {
    gap: Spacing.three,
  },
  logScroll: {
    maxHeight: 560,
  },
  logCard: {
    gap: 2,
  },
  logHeaderRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: 4,
  },
  logTitle: {
    fontSize: 15,
    fontWeight: '800',
  },
  logSub: {
    fontSize: 11.5,
    marginBottom: 2,
  },
  logResult: {
    fontSize: 12.5,
    fontWeight: '700',
    marginBottom: 4,
  },
  logScore: {
    fontSize: 12,
  },
  seasonCard: {
    gap: 6,
  },
  seasonTitle: {
    fontSize: 17,
    fontWeight: '800',
    marginBottom: 2,
  },
  seasonResultRow: {
    flexDirection: 'row',
    gap: Spacing.three,
  },
  flex1: {
    flex: 1,
    minWidth: 0,
  },
  seasonLabel: {
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginBottom: 2,
  },
  seasonValue: {
    fontSize: 13,
    fontWeight: '700',
  },
  playoffList: {
    marginTop: 2,
  },
  playoffRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: Spacing.two,
    paddingVertical: 6,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  playoffStage: {
    fontSize: 12,
    fontWeight: '700',
  },
  playoffResult: {
    fontSize: 12.5,
    fontWeight: '800',
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginTop: Spacing.two,
    marginBottom: 2,
  },
  tableHeaderRow: {
    flexDirection: 'row',
    paddingBottom: 6,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  tableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    borderRadius: Radius.sm,
    paddingHorizontal: 4,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  cell: {
    fontSize: 12,
    textAlign: 'right',
  },
  posCol: {
    width: 24,
    textAlign: 'left',
    fontWeight: '700',
  },
  teamCol: {
    flex: 1,
    textAlign: 'left',
  },
  teamName: {
    fontWeight: '700',
  },
  numCol: {
    width: 56,
    fontWeight: '700',
  },
  leaderGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.three,
  },
  leaderCard: {
    flexGrow: 1,
    flexBasis: 280,
    minWidth: 240,
    overflow: 'hidden',
  },
  leaderAccent: {
    position: 'absolute',
    top: 0,
    left: 0,
    bottom: 0,
    width: 4,
  },
  leaderTitle: {
    fontSize: 13,
    fontWeight: '800',
    marginBottom: 4,
    marginLeft: Spacing.two,
  },
  allTimeList: {
    maxHeight: 260,
  },
  leaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.two,
    paddingVertical: 8,
    paddingLeft: Spacing.two,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  leaderRank: {
    width: 18,
    fontSize: 12,
    fontWeight: '800',
  },
  leaderName: {
    fontSize: 12.5,
    fontWeight: '700',
  },
  leaderTeam: {
    fontSize: 10.5,
    marginTop: 1,
  },
  leaderValue: {
    fontSize: 14,
    fontWeight: '800',
  },
  emptyText: {
    fontSize: 12,
    paddingVertical: Spacing.two,
  },
});
