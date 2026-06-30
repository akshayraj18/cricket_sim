import { useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useLayout } from '@/hooks/use-layout';

import { PlayerDict } from '@/api/types';
import { NoActiveCareer } from '@/components/empty-state';
import { PlayerProfileSheet } from '@/components/player-profile-sheet';
import { ScreenHeader } from '@/components/screen-header';
import { ThemedText } from '@/components/themed-text';
import { Card } from '@/components/ui/card';
import { Dropdown, DropdownOption } from '@/components/ui/dropdown';
import { SegmentedControl } from '@/components/ui/segmented-control';
import { ContentBottomInset, getLegibleAccentValue, getTeamSwatch, Radius, Spacing } from '@/constants/theme';
import { useCareer } from '@/context/CareerContext';
import { useError } from '@/context/ErrorContext';
import { useLeague } from '@/context/LeagueContext';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { promptRename } from '@/hooks/use-rename';
import { useTheme } from '@/hooks/use-theme';

/** Display a leaderboard stat value: round floats to one decimal (dropping a
 * trailing .0) so MVP scores read "2152.9" not "2152.8999999999996". */
function formatStat(value: PlayerDict[keyof PlayerDict] | undefined): string {
  if (value == null) return '-';
  if (typeof value === 'number') {
    return Number.isInteger(value) ? String(value) : String(Math.round(value * 10) / 10);
  }
  return String(value);
}

type StatsTab = 'batting' | 'bowling' | 'leaders' | 'names';

const TABS: { key: StatsTab; label: string }[] = [
  { key: 'batting', label: 'Batting' },
  { key: 'bowling', label: 'Bowling' },
  { key: 'leaders', label: 'Leaders' },
  { key: 'names', label: 'Names' },
];

const BAT_COLUMNS: { key: keyof PlayerDict; label: string }[] = [
  { key: 'runs', label: 'Runs' },
  { key: 'balls', label: 'B' },
  { key: 'avg', label: 'Avg' },
  { key: 'sr', label: 'SR' },
  { key: 'hs', label: 'HS' },
  { key: 'fours', label: '4s' },
  { key: 'sixes', label: '6s' },
  { key: 'fifties', label: '50s' },
  { key: 'hundreds', label: '100s' },
  { key: 'mvp', label: 'MVP' },
];

const BOWL_COLUMNS: { key: keyof PlayerDict; label: string }[] = [
  { key: 'wickets', label: 'Wkts' },
  { key: 'balls_bowled', label: 'B' },
  { key: 'runs_conceded', label: 'Runs' },
  { key: 'econ', label: 'Econ' },
  { key: 'bowling_avg', label: 'Avg' },
  { key: 'bowling_sr', label: 'SR' },
  { key: 'best_bowling', label: 'Best' },
  { key: 'catches', label: 'Ct' },
  { key: 'mvp', label: 'MVP' },
];

const BAT_LEADER_DEFS: { title: string; listKey: string; statKey: keyof PlayerDict; color: string }[] = [
  { title: 'Orange Cap', listKey: 'orange_cap', statKey: 'runs', color: '#f97316' },
  { title: 'MVP Race', listKey: 'mvp', statKey: 'mvp', color: '#0f172a' },
  { title: 'Most Sixes', listKey: 'sixes', statKey: 'sixes', color: '#dc2626' },
  { title: 'Most Fours', listKey: 'fours', statKey: 'fours', color: '#2563eb' },
  { title: 'Most Boundaries', listKey: 'boundaries', statKey: 'boundaries', color: '#059669' },
  { title: 'Highest Score', listKey: 'highest_score', statKey: 'hs', color: '#b45309' },
  { title: 'Best Strike Rate', listKey: 'strike_rate', statKey: 'sr', color: '#db2777' },
];

const BOWL_LEADER_DEFS: { title: string; listKey: string; statKey: keyof PlayerDict; color: string }[] = [
  { title: 'Purple Cap', listKey: 'purple_cap', statKey: 'wickets', color: '#7c3aed' },
  { title: 'Best Economy', listKey: 'economy', statKey: 'econ', color: '#0891b2' },
  { title: 'Best Bowling', listKey: 'best_figures', statKey: 'best_bowling', color: '#6d28d9' },
  { title: 'Most Catches', listKey: 'catches', statKey: 'catches', color: '#16a34a' },
  { title: 'Most Stumpings', listKey: 'stumpings', statKey: 'stumpings', color: '#0d9488' },
  { title: 'Most Run Outs', listKey: 'runouts', statKey: 'runouts', color: '#ca8a04' },
];

export default function StatsScreen() {
  const theme = useTheme();
  const { contentContainerStyle } = useLayout();
  const { activeCareerId, activeCareer } = useCareer();
  const { payload, loading, error, setPayload } = useLeague();
  const { showError } = useError();

  const handleRename = (kind: 'team' | 'player', currentName: string) => {
    if (!activeCareerId) return;
    promptRename({ careerId: activeCareerId, kind, currentName, onRenamed: setPayload, onError: showError });
  };
  const [tab, setTab] = useState<StatsTab>('batting');
  const [search, setSearch] = useState('');
  const [teamFilter, setTeamFilter] = useState<string | null>(null);
  const [profilePlayer, setProfilePlayer] = useState<PlayerDict | null>(null);
  const [batSort, setBatSort] = useState<{ key: keyof PlayerDict; dir: 1 | -1 }>({ key: 'runs', dir: -1 });
  const [bowlSort, setBowlSort] = useState<{ key: keyof PlayerDict; dir: 1 | -1 }>({ key: 'wickets', dir: -1 });

  const scheme = useColorScheme();
  const accent = payload ? getTeamSwatch(payload.user_team ?? '', scheme) : undefined;

  const teamOptions: DropdownOption[] = useMemo(
    () => [
      { value: '', label: 'All Teams' },
      ...(payload?.teams ?? []).map((t) => ({
        value: t.name,
        label: `${t.abbr} · ${t.name}`,
        color: getTeamSwatch(t.name, scheme),
      })),
    ],
    [payload?.teams, scheme]
  );

  const allPlayers = useMemo(() => payload?.teams.flatMap((t) => t.roster) ?? [], [payload]);

  const foundPlayer = useMemo(() => {
    if (!search.trim()) return null;
    const q = search.toLowerCase();
    return allPlayers.find((p) => p.name.toLowerCase().includes(q)) ?? null;
  }, [search, allPlayers]);

  const batRows = useMemo(() => {
    if (!payload) return [];
    const rows = payload.tables.batting.filter((p) => !teamFilter || p.team === teamFilter);
    return sortPlayers(rows, batSort);
  }, [payload, teamFilter, batSort]);

  const bowlRows = useMemo(() => {
    if (!payload) return [];
    const rows = payload.tables.bowling.filter((p) => !teamFilter || p.team === teamFilter);
    return sortPlayers(rows, bowlSort);
  }, [payload, teamFilter, bowlSort]);

  if (!activeCareerId) {
    return (
      <View style={[styles.container, { backgroundColor: theme.bg }]}>
        <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
          <View style={[styles.body, contentContainerStyle]}>
            <ScreenHeader title="Stats" />
            <NoActiveCareer />
          </View>
        </SafeAreaView>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
        <View style={[styles.body, contentContainerStyle]}>
        <ScreenHeader eyebrow={activeCareer?.name} title="Stats" />
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
            <View style={[styles.searchRow, { backgroundColor: theme.bgElevated, borderColor: theme.border }]}>
              <TextInput
                value={search}
                onChangeText={setSearch}
                placeholder="Search players…"
                placeholderTextColor={theme.textFaint}
                style={[styles.searchInput, { color: theme.text }]}
              />
            </View>

            {foundPlayer && (
              <Pressable onPress={() => setProfilePlayer(foundPlayer)}>
                <Card style={styles.profileCard}>
                  <ThemedText style={styles.profileName}>{foundPlayer.name}</ThemedText>
                  <ThemedText themeColor="textDim" style={styles.profileSub}>
                    {foundPlayer.team} · {foundPlayer.role} · Form {foundPlayer.form} · OVR {foundPlayer.ovr_progression}
                  </ThemedText>
                  <View style={styles.chipRow}>
                    <StatChip label="Runs" value={foundPlayer.runs} />
                    <StatChip label="SR" value={foundPlayer.sr} />
                    <StatChip label="Wkts" value={foundPlayer.wickets} />
                    <StatChip label="Econ" value={foundPlayer.econ} />
                    <StatChip label="Ct/St/RO" value={`${foundPlayer.catches}/${foundPlayer.stumpings}/${foundPlayer.runouts}`} />
                    <StatChip label="MVP" value={foundPlayer.mvp} />
                  </View>
                  <ThemedText themeColor="textFaint" style={styles.profileNotes}>
                    {foundPlayer.strengths} · {foundPlayer.weaknesses}
                  </ThemedText>
                </Card>
              </Pressable>
            )}

            <Dropdown
              label="Team"
              value={teamFilter ?? ''}
              options={teamOptions}
              onChange={(v) => setTeamFilter(v || null)}
              accentColor={accent}
            />

            <SegmentedControl segments={TABS} value={tab} onChange={setTab} accentColor={accent} />

            {tab === 'batting' && (
              <StatsTable
                rows={batRows}
                columns={BAT_COLUMNS}
                sort={batSort}
                onSort={setBatSort}
                onPlayerPress={setProfilePlayer}
              />
            )}
            {tab === 'bowling' && (
              <StatsTable
                rows={bowlRows}
                columns={BOWL_COLUMNS}
                sort={bowlSort}
                onSort={setBowlSort}
                onPlayerPress={setProfilePlayer}
              />
            )}
            {tab === 'leaders' && (
              <View style={styles.leaderGrid}>
                {BAT_LEADER_DEFS.map((def) => (
                  <LeaderboardCard
                    key={def.listKey}
                    title={def.title}
                    rows={(payload.leaderboards[def.listKey] || []).filter((p) => !teamFilter || p.team === teamFilter)}
                    statKey={def.statKey}
                    color={def.color}
                    onPlayerPress={setProfilePlayer}
                    against={def.title === 'Highest Score' ? 'hs_against' : undefined}
                  />
                ))}
                {BOWL_LEADER_DEFS.map((def) => (
                  <LeaderboardCard
                    key={def.listKey}
                    title={def.title}
                    rows={(payload.leaderboards[def.listKey] || []).filter((p) => !teamFilter || p.team === teamFilter)}
                    statKey={def.statKey}
                    color={def.color}
                    onPlayerPress={setProfilePlayer}
                    against={def.title === 'Best Bowling' ? 'best_bowling_against' : undefined}
                  />
                ))}
              </View>
            )}
            {tab === 'names' && (
              <NamesEditor
                teams={payload.teams.filter((t) => !teamFilter || t.name === teamFilter)}
                onRename={handleRename}
              />
            )}
          </ScrollView>
        )}

        <PlayerProfileSheet player={profilePlayer} onClose={() => setProfilePlayer(null)} accentColor={accent} />
        </View>
      </SafeAreaView>
    </View>
  );
}

function sortPlayers(players: PlayerDict[], sort: { key: keyof PlayerDict; dir: 1 | -1 }): PlayerDict[] {
  return [...players].sort((a, b) => {
    const av = a[sort.key];
    const bv = b[sort.key];
    let result: number;
    if (typeof av === 'string' || typeof bv === 'string') {
      result = String(av ?? '').localeCompare(String(bv ?? ''), undefined, { numeric: true, sensitivity: 'base' });
    } else {
      result = (Number(av) || 0) - (Number(bv) || 0);
    }
    return result * sort.dir;
  });
}

function StatChip({ label, value }: { label: string; value: string | number }) {
  const theme = useTheme();
  return (
    <View style={[styles.statChip, { backgroundColor: theme.badgeBg }]}>
      <ThemedText themeColor="textDim" style={styles.statChipLabel}>
        {label}
      </ThemedText>
      <ThemedText style={styles.statChipValue}>{value}</ThemedText>
    </View>
  );
}

function StatsTable({
  rows,
  columns,
  sort,
  onSort,
  onPlayerPress,
}: {
  rows: PlayerDict[];
  columns: { key: keyof PlayerDict; label: string }[];
  sort: { key: keyof PlayerDict; dir: 1 | -1 };
  onSort: (s: { key: keyof PlayerDict; dir: 1 | -1 }) => void;
  onPlayerPress: (p: PlayerDict) => void;
}) {
  const theme = useTheme();

  const toggleSort = (key: keyof PlayerDict) => {
    if (sort.key === key) onSort({ key, dir: sort.dir === 1 ? -1 : 1 });
    else onSort({ key, dir: -1 });
  };

  return (
    <Card style={styles.tableCard}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View>
          <View style={[styles.tableHeaderRow, { borderBottomColor: theme.border, backgroundColor: theme.bgCard }]}>
            <ThemedText themeColor="textFaint" style={[styles.tableHeaderCell, styles.rankCol]}>
              #
            </ThemedText>
            <ThemedText themeColor="textFaint" style={[styles.tableHeaderCell, styles.nameCol]}>
              Player
            </ThemedText>
            <ThemedText themeColor="textFaint" style={[styles.tableHeaderCell, styles.teamColHeader]}>
              Team
            </ThemedText>
            {columns.map((c) => (
              <Pressable key={String(c.key)} onPress={() => toggleSort(c.key)}>
                <ThemedText
                  themeColor={sort.key === c.key ? undefined : 'textFaint'}
                  style={[styles.tableHeaderCell, styles.dataCol]}>
                  {c.label}
                  {sort.key === c.key ? (sort.dir === 1 ? ' ▲' : ' ▼') : ''}
                </ThemedText>
              </Pressable>
            ))}
          </View>
          <ScrollView style={styles.tableBody} nestedScrollEnabled showsVerticalScrollIndicator={false}>
            {rows.map((p, i) => (
              <Pressable key={p.name} onPress={() => onPlayerPress(p)} style={[styles.tableRow, { borderBottomColor: theme.border }]}>
                <ThemedText style={[styles.tableCell, styles.rankCol]}>{i + 1}</ThemedText>
                <ThemedText style={[styles.tableCell, styles.tableName, styles.nameCol]} numberOfLines={1}>
                  {p.name}
                </ThemedText>
                <ThemedText themeColor="textDim" style={[styles.tableCell, styles.teamColHeader]} numberOfLines={1}>
                  {p.team ? p.team.slice(0, 3).toUpperCase() : '-'}
                </ThemedText>
                {columns.map((c) => (
                  <ThemedText key={String(c.key)} style={[styles.tableCell, styles.dataCol]}>
                    {String(p[c.key] ?? '-')}
                  </ThemedText>
                ))}
              </Pressable>
            ))}
            {rows.length === 0 && (
              <ThemedText themeColor="textDim" style={styles.emptyText}>
                No data yet.
              </ThemedText>
            )}
          </ScrollView>
        </View>
      </ScrollView>
    </Card>
  );
}

function LeaderboardCard({
  title,
  rows,
  statKey,
  color,
  onPlayerPress,
  against,
}: {
  title: string;
  rows: PlayerDict[];
  statKey: keyof PlayerDict;
  color: string;
  onPlayerPress: (p: PlayerDict) => void;
  against?: 'hs_against' | 'best_bowling_against';
}) {
  const theme = useTheme();
  const scheme = useColorScheme();
  // The accent (e.g. MVP Race's near-black slate) can vanish as value text in
  // dark mode; force it legible while keeping the stripe vivid.
  const valueColor = getLegibleAccentValue(color, scheme);
  return (
    <Card style={styles.leaderCard}>
      <View style={[styles.leaderAccent, { backgroundColor: color }]} />
      <ThemedText style={styles.leaderTitle}>{title}</ThemedText>
      <ScrollView style={styles.leaderList} nestedScrollEnabled showsVerticalScrollIndicator={false}>
        {rows.map((p, i) => {
          const againstText = against && p[against] ? ` vs ${p[against]}` : '';
          return (
            <Pressable key={p.name} onPress={() => onPlayerPress(p)} style={[styles.leaderRow, { borderBottomColor: theme.border }]}>
              <ThemedText themeColor="textFaint" style={styles.leaderRank}>
                {i + 1}
              </ThemedText>
              <View style={styles.flex1}>
                <ThemedText style={styles.leaderName} numberOfLines={1}>
                  {p.name}
                </ThemedText>
                <ThemedText themeColor="textFaint" style={styles.leaderTeam} numberOfLines={1}>
                  {p.team}
                  {againstText}
                </ThemedText>
              </View>
              <ThemedText style={[styles.leaderValue, { color: valueColor }]}>{formatStat(p[statKey])}</ThemedText>
            </Pressable>
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

function NamesEditor({
  teams,
  onRename,
}: {
  teams: NonNullable<ReturnType<typeof useLeague>['payload']>['teams'];
  onRename: (kind: 'team' | 'player', currentName: string) => void;
}) {
  const theme = useTheme();
  return (
    <View style={styles.namesWrap}>
      <ThemedText themeColor="textDim" style={styles.namesHint}>
        Tap a team or player to rename them. Changes apply across your whole career — use this to set your
        own names for any club or player.
      </ThemedText>
      {teams.map((t) => (
        <Card key={t.name} style={styles.namesCard}>
          <Pressable onPress={() => onRename('team', t.name)} style={styles.nameRow}>
            <ThemedText style={styles.namesTeam} numberOfLines={1}>
              {t.abbr} · {t.name}
            </ThemedText>
            <ThemedText themeColor="green" style={styles.namePencil}>
              ✎
            </ThemedText>
          </Pressable>
          {[...t.roster]
            .sort((a, b) => b.ovr - a.ovr)
            .map((p) => (
              <Pressable
                key={p.name}
                onPress={() => onRename('player', p.name)}
                style={[styles.nameRow, styles.namePlayerRow, { borderTopColor: theme.border }]}>
                <ThemedText style={styles.namePlayer} numberOfLines={1}>
                  {p.name}
                </ThemedText>
                <ThemedText themeColor="textDim" style={styles.namePencil}>
                  ✎
                </ThemedText>
              </Pressable>
            ))}
        </Card>
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
  searchRow: {
    borderRadius: Radius.sm,
    borderWidth: 1,
    paddingHorizontal: Spacing.three,
  },
  searchInput: {
    height: 42,
    fontSize: 14,
  },
  profileCard: {
    gap: 4,
  },
  profileName: {
    fontSize: 16,
    fontWeight: '800',
  },
  profileSub: {
    fontSize: 12,
    marginBottom: 4,
  },
  profileNotes: {
    fontSize: 11.5,
    marginTop: 4,
    lineHeight: 16,
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  statChip: {
    borderRadius: Radius.sm,
    paddingHorizontal: 8,
    paddingVertical: 4,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statChipLabel: {
    fontSize: 10.5,
    fontWeight: '600',
  },
  statChipValue: {
    fontSize: 12,
    fontWeight: '800',
  },
  tableCard: {
    paddingHorizontal: Spacing.two,
    paddingVertical: Spacing.two,
  },
  tableHeaderRow: {
    flexDirection: 'row',
    paddingBottom: 6,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  tableBody: {
    maxHeight: 480,
  },
  tableHeaderCell: {
    fontSize: 10,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.4,
    textAlign: 'right',
  },
  tableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 9,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  tableCell: {
    fontSize: 12,
    textAlign: 'right',
  },
  tableName: {
    fontWeight: '700',
    textAlign: 'left',
  },
  rankCol: {
    width: 26,
    textAlign: 'left',
  },
  nameCol: {
    width: 150,
    textAlign: 'left',
    paddingRight: Spacing.two,
  },
  teamColHeader: {
    width: 50,
  },
  dataCol: {
    width: 56,
  },
  emptyText: {
    fontSize: 12,
    paddingVertical: Spacing.two,
  },
  leaderGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.three,
  },
  namesWrap: {
    gap: Spacing.three,
  },
  namesHint: {
    fontSize: 12.5,
    lineHeight: 18,
  },
  namesCard: {
    paddingVertical: Spacing.one,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
    gap: Spacing.two,
  },
  namePlayerRow: {
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  namesTeam: {
    flex: 1,
    fontSize: 14,
    fontWeight: '800',
  },
  namePlayer: {
    flex: 1,
    fontSize: 13.5,
    fontWeight: '500',
  },
  namePencil: {
    fontSize: 15,
    fontWeight: '700',
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
  leaderList: {
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
  flex1: {
    flex: 1,
    minWidth: 0,
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
});
