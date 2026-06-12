import { useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, TextInput, View } from 'react-native';

import { seasonApi } from '@/api/season';
import { LeaguePayload, PlayerDict } from '@/api/types';
import { PlayerProfileSheet } from '@/components/player-profile-sheet';
import { ThemedText } from '@/components/themed-text';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Pill } from '@/components/ui/pill';
import { SegmentedControl } from '@/components/ui/segmented-control';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { ORDER_ZONES, slotZoneLabel, uniqueXi } from '@/utils/lineup';

type DraftTab = 'available' | 'order' | 'squad';

const ZONE_FILTERS = ['All Slots', ...ORDER_ZONES.map((z) => z.label)];

const TABS: { key: DraftTab; label: string }[] = [
  { key: 'available', label: 'Available' },
  { key: 'order', label: 'Draft Order' },
  { key: 'squad', label: 'My Squad' },
];

export function DraftHub({
  careerId,
  payload,
  accent,
  onChange,
}: {
  careerId: string;
  payload: LeaguePayload;
  accent?: string;
  onChange: (payload: LeaguePayload) => void;
}) {
  const theme = useTheme();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profilePlayer, setProfilePlayer] = useState<PlayerDict | null>(null);
  const [roleFilter, setRoleFilter] = useState('All Roles');
  const [zoneFilter, setZoneFilter] = useState('All Slots');
  const [tab, setTab] = useState<DraftTab>('available');
  const [search, setSearch] = useState('');

  const draft = payload.draft;
  const draftStarted = draft.started !== false;
  const userTeam = payload.teams.find((t) => t.name === payload.user_team);
  const isUserTurn = draftStarted && draft.current_team === payload.user_team;

  const roles = useMemo(() => {
    const set = new Set(draft.available.map((p) => p.role));
    return ['All Roles', ...Array.from(set)];
  }, [draft.available]);

  const players = useMemo(() => {
    let filtered =
      roleFilter === 'All Roles' ? draft.available : draft.available.filter((p) => p.role === roleFilter);
    if (zoneFilter !== 'All Slots') {
      filtered = filtered.filter((p) => slotZoneLabel(p.preferred_position) === zoneFilter);
    }
    const query = search.trim().toLowerCase();
    if (query) {
      filtered = filtered.filter((p) => p.name.toLowerCase().includes(query));
    }
    return [...filtered].sort((a, b) => b.ovr - a.ovr);
  }, [draft.available, roleFilter, zoneFilter, search]);

  const draftOrder = useMemo(() => [...draft.history].reverse(), [draft.history]);

  // A planning preview of the user's drafted squad slotted into a best XI by
  // natural batting position, grouped into Openers / Middle / Death / Tail.
  // `starting_xi` arrives from the backend already in natural batting order.
  const previewZones = useMemo(() => {
    const roster = userTeam?.roster ?? [];
    if (roster.length < 11) return [];
    const byName = new Map(roster.map((p) => [p.name, p]));
    const xiNames = uniqueXi(userTeam?.starting_xi ?? [], roster);
    const slotted = xiNames.map((name, i) => ({ player: byName.get(name), slot: i + 1 })).filter((s) => s.player);
    return ORDER_ZONES.map((zone) => ({
      zone,
      players: slotted.filter((s) => s.slot >= zone.range[0] && s.slot <= zone.range[1]),
    })).filter((g) => g.players.length > 0);
  }, [userTeam]);

  const wrap = async (fn: () => Promise<LeaguePayload>) => {
    setBusy(true);
    setError(null);
    try {
      onChange(await fn());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setBusy(false);
    }
  };

  if (!draftStarted) {
    return (
      <View style={styles.content}>
        <Card>
          <ThemedText style={styles.title}>Mega Draft Setup</ThemedText>
          <ThemedText themeColor="textDim" style={styles.helpText}>
            You selected {payload.user_team} as a blank franchise. The draft order is set, and you are drafting{' '}
            {ordinal(draft.user_pick_position || 0)} in a snake draft with premier IPL players.
          </ThemedText>
          <Button
            label="Start Draft"
            variant="primary"
            accentColor={accent}
            loading={busy}
            onPress={() => wrap(() => seasonApi.startDraft(careerId))}
          />
        </Card>
        {error && <ThemedText themeColor="red">{error}</ThemedText>}
      </View>
    );
  }

  return (
    <View style={styles.content}>
      <Card>
        <ThemedText style={styles.title}>
          {payload.draft_type === 'mega' ? 'Mega Snake Draft' : 'Reverse-Standings Draft'}
        </ThemedText>
        <ThemedText themeColor="textDim" style={styles.helpText}>
          Round {draft.round}, Pick {draft.pick} · On the clock: {draft.current_team}
        </ThemedText>
        {error && (
          <ThemedText themeColor="red" style={styles.helpText}>
            {error}
          </ThemedText>
        )}
        <View style={styles.buttonRow}>
          <Button
            label="Autodraft Pick"
            variant="secondary"
            small
            loading={busy}
            onPress={() => wrap(() => seasonApi.autodraft(careerId, 'user'))}
          />
          <Button
            label="Autodraft Entire Draft"
            variant="ghost"
            accentColor={theme.red}
            small
            loading={busy}
            onPress={() => wrap(() => seasonApi.autodraft(careerId, 'all'))}
          />
        </View>
      </Card>

      {Object.keys(draft.needs || {}).length > 0 && (
        <Card>
          <ThemedText style={styles.sectionLabel}>Roster Needs</ThemedText>
          <View style={styles.pillRow}>
            {Object.entries(draft.needs).map(([k, v]) => (
              <Pill key={k} label={`${k.toUpperCase()}: ${v}`} accentColor={accent} />
            ))}
          </View>
        </Card>
      )}

      <SegmentedControl segments={TABS} value={tab} onChange={setTab} accentColor={accent} />

      {tab === 'available' && (
        <Card style={styles.listCard}>
          <TextInput
            value={search}
            onChangeText={setSearch}
            placeholder="Search players by name"
            placeholderTextColor={theme.textFaint}
            autoCapitalize="none"
            autoCorrect={false}
            clearButtonMode="while-editing"
            style={[
              styles.searchInput,
              { color: theme.text, borderColor: theme.border, backgroundColor: theme.bgElevated },
            ]}
          />
          <View style={styles.pillRow}>
            {roles.map((r) => (
              <Pressable key={r} onPress={() => setRoleFilter(r)}>
                <Pill label={r} accentColor={roleFilter === r ? accent : undefined} />
              </Pressable>
            ))}
          </View>
          <View style={styles.pillRow}>
            {ZONE_FILTERS.map((z) => (
              <Pressable key={z} onPress={() => setZoneFilter(z)}>
                <Pill label={z} accentColor={zoneFilter === z ? accent : undefined} />
              </Pressable>
            ))}
          </View>
          <ScrollView style={styles.scrollList} nestedScrollEnabled showsVerticalScrollIndicator={false}>
            {players.map((p) => (
              <View key={p.name} style={[styles.playerRow, { borderBottomColor: theme.border }]}>
                <Pressable style={styles.flex1} onPress={() => setProfilePlayer(p)}>
                  <ThemedText style={styles.playerName} numberOfLines={1}>
                    {p.name}
                  </ThemedText>
                  <ThemedText themeColor="textDim" style={styles.playerSub} numberOfLines={1}>
                    {p.role} · OVR {p.ovr} · Bat {p.bat}/Bowl {p.bowl} · {slotZoneLabel(p.preferred_position)} ·{' '}
                    {p.overseas ? 'Overseas' : 'Indian'}
                  </ThemedText>
                </Pressable>
                {isUserTurn && (
                  <Button
                    label="Pick"
                    variant="primary"
                    accentColor={accent}
                    small
                    loading={busy}
                    onPress={() => wrap(() => seasonApi.draftPick(careerId, p.name))}
                    style={styles.pickButton}
                  />
                )}
              </View>
            ))}
            {players.length === 0 && (
              <ThemedText themeColor="textDim" style={styles.emptyText}>
                No players match this filter.
              </ThemedText>
            )}
          </ScrollView>
        </Card>
      )}

      {tab === 'order' && (
        <Card style={styles.listCard}>
          <ThemedText style={styles.sectionLabel}>All Picks (most recent first)</ThemedText>
          <ScrollView style={styles.scrollList} nestedScrollEnabled showsVerticalScrollIndicator={false}>
            {draftOrder.map((h) => (
              <View key={`${h.round}-${h.pick}`} style={[styles.playerRow, { borderBottomColor: theme.border }]}>
                <View style={styles.pickBadge}>
                  <ThemedText style={styles.pickBadgeText}>{h.pick}</ThemedText>
                </View>
                <View style={styles.flex1}>
                  <ThemedText style={styles.playerName} numberOfLines={1}>
                    {h.player}
                  </ThemedText>
                  <ThemedText themeColor="textDim" style={styles.playerSub} numberOfLines={1}>
                    Round {h.round} · {h.team} · {h.role} · OVR {h.ovr}
                  </ThemedText>
                </View>
              </View>
            ))}
            {draftOrder.length === 0 && (
              <ThemedText themeColor="textDim" style={styles.emptyText}>
                No picks made yet.
              </ThemedText>
            )}
          </ScrollView>
        </Card>
      )}

      {tab === 'squad' && previewZones.length > 0 && (
        <Card style={styles.listCard}>
          <ThemedText style={styles.sectionLabel}>Drafted XI Preview</ThemedText>
          <ThemedText themeColor="textDim" style={styles.helpText}>
            A planning preview — your best XI auto-slotted by where each player naturally bats. Final XIs are set
            on My Squad.
          </ThemedText>
          {previewZones.map(({ zone, players: zonePlayers }) => (
            <View key={zone.key} style={styles.zoneGroup}>
              <ThemedText themeColor="textFaint" style={styles.zoneLabel}>
                {zone.label}
              </ThemedText>
              {zonePlayers.map(({ player, slot }) => (
                <Pressable
                  key={player!.name}
                  onPress={() => setProfilePlayer(player!)}
                  style={[styles.playerRow, { borderBottomColor: theme.border }]}>
                  <View style={styles.pickBadge}>
                    <ThemedText style={styles.pickBadgeText}>{slot}</ThemedText>
                  </View>
                  <View style={styles.flex1}>
                    <ThemedText style={styles.playerName} numberOfLines={1}>
                      {player!.name}
                    </ThemedText>
                    <ThemedText themeColor="textDim" style={styles.playerSub} numberOfLines={1}>
                      {player!.role} · OVR {player!.ovr} · Bat {player!.bat}/Bowl {player!.bowl} ·{' '}
                      {player!.overseas ? 'Overseas' : 'Indian'}
                    </ThemedText>
                  </View>
                </Pressable>
              ))}
            </View>
          ))}
        </Card>
      )}

      {tab === 'squad' && (
        <Card style={styles.listCard}>
          <ThemedText style={styles.sectionLabel}>My Drafted Squad ({userTeam?.roster.length ?? 0})</ThemedText>
          <ScrollView style={styles.scrollList} nestedScrollEnabled showsVerticalScrollIndicator={false}>
            {(userTeam?.roster ?? []).map((p) => (
              <Pressable
                key={p.name}
                onPress={() => setProfilePlayer(p)}
                style={[styles.playerRow, { borderBottomColor: theme.border }]}>
                <View style={styles.flex1}>
                  <ThemedText style={styles.playerName} numberOfLines={1}>
                    {p.name}
                  </ThemedText>
                  <ThemedText themeColor="textDim" style={styles.playerSub} numberOfLines={1}>
                    {p.role} · OVR {p.ovr} · Bat {p.bat}/Bowl {p.bowl} · {slotZoneLabel(p.preferred_position)} ·{' '}
                    {p.overseas ? 'Overseas' : 'Indian'}
                  </ThemedText>
                </View>
              </Pressable>
            ))}
            {(userTeam?.roster.length ?? 0) === 0 && (
              <ThemedText themeColor="textDim" style={styles.emptyText}>
                No players drafted yet.
              </ThemedText>
            )}
          </ScrollView>
        </Card>
      )}

      <PlayerProfileSheet player={profilePlayer} onClose={() => setProfilePlayer(null)} accentColor={accent} />
    </View>
  );
}

function ordinal(n: number): string {
  if (!n) return '-';
  const rem100 = n % 100;
  if (rem100 >= 10 && rem100 <= 20) return `${n}th`;
  const suffix = { 1: 'st', 2: 'nd', 3: 'rd' }[n % 10] ?? 'th';
  return `${n}${suffix}`;
}

const styles = StyleSheet.create({
  content: {
    gap: Spacing.three,
  },
  title: {
    fontSize: 16,
    fontWeight: '800',
    marginBottom: 4,
  },
  helpText: {
    fontSize: 12.5,
    lineHeight: 18,
    marginBottom: Spacing.two,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: Spacing.two,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: Spacing.two,
  },
  zoneGroup: {
    marginBottom: Spacing.two,
  },
  zoneLabel: {
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginTop: Spacing.two,
    marginBottom: 2,
  },
  searchInput: {
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 10,
    paddingHorizontal: Spacing.three,
    paddingVertical: 9,
    fontSize: 13.5,
    marginBottom: Spacing.two,
  },
  pillRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: Spacing.two,
  },
  listCard: {
    paddingBottom: 4,
  },
  scrollList: {
    maxHeight: 420,
  },
  playerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.two,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  flex1: {
    flex: 1,
    minWidth: 0,
  },
  playerName: {
    fontSize: 13.5,
    fontWeight: '700',
  },
  playerSub: {
    fontSize: 11,
    marginTop: 2,
  },
  pickButton: {
    flex: 0,
    paddingHorizontal: Spacing.three,
  },
  pickBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(127,127,127,0.15)',
  },
  pickBadgeText: {
    fontSize: 11,
    fontWeight: '800',
  },
  emptyText: {
    fontSize: 12.5,
    textAlign: 'center',
    paddingVertical: Spacing.three,
  },
});
