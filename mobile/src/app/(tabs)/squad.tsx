import { useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useLayout } from '@/hooks/use-layout';

import { seasonApi } from '@/api/season';
import { PlayerDict } from '@/api/types';
import { NoActiveCareer } from '@/components/empty-state';
import { PlayerPickerModal } from '@/components/player-picker-modal';
import { PlayerProfileSheet } from '@/components/player-profile-sheet';
import { PlayerRow } from '@/components/player-row';
import { ScreenHeader } from '@/components/screen-header';
import { ThemedText } from '@/components/themed-text';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Pill } from '@/components/ui/pill';
import { SegmentedControl } from '@/components/ui/segmented-control';
import { ContentBottomInset, getTeamBackground, getTeamPlayerAccent, Radius, Spacing } from '@/constants/theme';
import { useCareer } from '@/context/CareerContext';
import { useError } from '@/context/ErrorContext';
import { useLeague } from '@/context/LeagueContext';
import { useTour } from '@/context/TourContext';
import { promptRename } from '@/hooks/use-rename';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { useTheme } from '@/hooks/use-theme';
import {
  ORDER_ZONES,
  OVER_PHASE_ZONES,
  autofillBowlingPlan,
  benchNames,
  bowlingOptions,
  bowlingPlanError,
  impactSubError,
  uniqueXi,
  xiValidationError,
} from '@/utils/lineup';

type SquadTab = 'roster' | 'batting' | 'bowling' | 'leadership';

const ALL_SQUAD_SEGMENTS: { key: SquadTab; label: string }[] = [
  { key: 'roster', label: 'Roster' },
  { key: 'batting', label: 'Starting XI' },
  { key: 'bowling', label: 'Bowling Plan' },
  { key: 'leadership', label: 'Leadership' },
];

type SortKey = 'ovr' | 'name' | 'role' | 'mvp';

export default function SquadScreen() {
  const theme = useTheme();
  const scheme = useColorScheme();
  const { activeCareerId, activeCareer } = useCareer();
  const { payload, loading, error, refresh, setPayload } = useLeague();
  const [tab, setTab] = useState<SquadTab>('roster');
  const { currentStep } = useTour();
  // While the guided tour is on a squad step that requests a specific sub-tab
  // (e.g. the Starting XI walkthrough), open it so the tour highlights the right
  // screen instead of whatever the user last had selected.
  const tourSquadTab = currentStep?.tab === 'squad' ? currentStep.squadTab : undefined;
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (tourSquadTab) setTab(tourSquadTab);
  }, [tourSquadTab]);
  const [profilePlayer, setProfilePlayer] = useState<PlayerDict | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>('ovr');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [editNames, setEditNames] = useState(false);
  const { showError } = useError();

  const team = useMemo(
    () => payload?.teams.find((t) => t.name === payload.user_team),
    [payload]
  );
  const accent = team ? getTeamPlayerAccent(team, scheme) : undefined;

  const squadSegments = useMemo(() => {
    const isBowlingPlanFormat = !payload?.match_format || payload.match_format === 't20';
    return isBowlingPlanFormat
      ? ALL_SQUAD_SEGMENTS
      : ALL_SQUAD_SEGMENTS.filter((s) => s.key !== 'bowling');
  }, [payload?.match_format]);

  const handleRename = (kind: 'team' | 'player', currentName: string) => {
    if (!activeCareerId) return;
    promptRename({ careerId: activeCareerId, kind, currentName, onRenamed: setPayload, onError: showError });
  };

  const sortedRoster = useMemo(() => {
    if (!team) return [];
    const list = [...team.roster];
    list.sort((a, b) => {
      switch (sortKey) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'role':
          return a.role.localeCompare(b.role);
        case 'mvp':
          return b.mvp - a.mvp;
        case 'ovr':
        default:
          return b.ovr - a.ovr;
      }
    });
    return list;
  }, [team, sortKey]);

  if (!activeCareerId) {
    return (
      <View style={[styles.container, { backgroundColor: theme.bg }]}>
        <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
          <View style={styles.body}>
            <ScreenHeader title="Squad" />
            <NoActiveCareer />
          </View>
        </SafeAreaView>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
        <View style={styles.body}>
        <ScreenHeader eyebrow={activeCareer?.name} title="Squad" />
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
        {!loading && !error && payload && team && (
          <>
            <View style={styles.segmentWrap}>
              <SegmentedControl segments={squadSegments} value={tab} onChange={setTab} accentColor={getTeamBackground(team, team.name)} />
            </View>

            {tab === 'roster' && (
              <View style={styles.editNamesRow}>
                <Pressable onPress={() => handleRename('team', team.name)} disabled={!editNames} hitSlop={8}>
                  <ThemedText style={[styles.teamNameHeading, editNames && { color: theme.green }]} numberOfLines={1}>
                    {team.name}
                    {editNames ? '  ✎' : ''}
                  </ThemedText>
                </Pressable>
                <Pressable onPress={() => setEditNames((v) => !v)} hitSlop={8}>
                  <ThemedText themeColor={editNames ? 'green' : 'textDim'} style={styles.editToggle}>
                    {editNames ? 'Done' : 'Edit Names'}
                  </ThemedText>
                </Pressable>
              </View>
            )}

            {saveError && (
              <View style={styles.errorBanner}>
                <ThemedText themeColor="red" style={styles.errorText}>
                  {saveError}
                </ThemedText>
              </View>
            )}

            {tab === 'roster' && (
              <RosterTab
                team={team}
                roster={sortedRoster}
                accent={accent}
                sortKey={sortKey}
                onSort={setSortKey}
                editNames={editNames}
                onRenamePlayer={(name) => handleRename('player', name)}
                onPlayerPress={setProfilePlayer}
              />
            )}

            {tab === 'batting' && (
              <BattingXiTab
                key={`batting-${team.name}`}
                careerId={activeCareerId}
                team={team}
                accent={accent}
                saving={saving}
                setSaving={setSaving}
                setSaveError={setSaveError}
                onPlayerPress={setProfilePlayer}
                refresh={refresh}
                competition={payload.competition}
              />
            )}

            {tab === 'bowling' && (
              <BowlingPlanTab
                key={`bowling-${team.name}`}
                careerId={activeCareerId}
                team={team}
                accent={accent}
                saving={saving}
                setSaving={setSaving}
                setSaveError={setSaveError}
                refresh={refresh}
              />
            )}

            {tab === 'leadership' && (
              <LeadershipTab
                key={`leadership-${team.name}`}
                careerId={activeCareerId}
                team={team}
                accent={accent}
                saving={saving}
                setSaving={setSaving}
                setSaveError={setSaveError}
                refresh={refresh}
              />
            )}
          </>
        )}

        <PlayerProfileSheet player={profilePlayer} onClose={() => setProfilePlayer(null)} accentColor={accent} />
        </View>
      </SafeAreaView>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Roster tab
// ---------------------------------------------------------------------------

function RosterTab({
  team,
  roster,
  accent,
  sortKey,
  onSort,
  editNames,
  onRenamePlayer,
  onPlayerPress,
}: {
  team: NonNullable<ReturnType<typeof useLeague>['payload']>['teams'][number];
  roster: PlayerDict[];
  editNames: boolean;
  onRenamePlayer: (name: string) => void;
  accent?: string;
  sortKey: SortKey;
  onSort: (key: SortKey) => void;
  onPlayerPress: (p: PlayerDict) => void;
}) {
  const { contentContainerStyle, bottomInset } = useLayout();
  const SORT_OPTIONS: { key: SortKey; label: string }[] = [
    { key: 'ovr', label: 'OVR' },
    { key: 'mvp', label: 'MVP' },
    { key: 'name', label: 'Name' },
    { key: 'role', label: 'Role' },
  ];

  return (
    <ScrollView contentContainerStyle={[styles.content, contentContainerStyle, { paddingBottom: bottomInset }]} showsVerticalScrollIndicator={false}>
      <View style={styles.rowBetween}>
        <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
          {roster.length}-Man Roster
        </ThemedText>
        <View style={styles.sortRow}>
          {SORT_OPTIONS.map((opt) => (
            <Pressable key={opt.key} onPress={() => onSort(opt.key)}>
              <Pill label={opt.label} accentColor={sortKey === opt.key ? accent : undefined} style={styles.sortPill} />
            </Pressable>
          ))}
        </View>
      </View>
      <Card style={styles.rosterCard}>
        {roster.map((player) => (
          <PlayerRow
            key={player.name}
            player={player}
            accentColor={accent}
            isCaptain={player.name === team.captain}
            isViceCaptain={player.name === team.vice_captain}
            isWicketkeeper={player.name === team.saved_wicketkeeper}
            onPress={() => (editNames ? onRenamePlayer(player.name) : onPlayerPress(player))}
            trailing={
              editNames ? <ThemedText themeColor="green" style={styles.rowPencil}>✎</ThemedText> : undefined
            }
          />
        ))}
      </Card>
    </ScrollView>
  );
}

// ---------------------------------------------------------------------------
// Starting XI tab — Starting XI (11) + Impact Sub (1)
// ---------------------------------------------------------------------------

function BattingXiTab({
  careerId,
  team,
  accent,
  saving,
  setSaving,
  setSaveError,
  onPlayerPress,
  refresh,
  competition,
}: {
  careerId: string;
  team: NonNullable<ReturnType<typeof useLeague>['payload']>['teams'][number];
  accent?: string;
  saving: boolean;
  setSaving: (v: boolean) => void;
  setSaveError: (v: string | null) => void;
  onPlayerPress: (p: PlayerDict) => void;
  refresh: () => Promise<void>;
  competition: string;
}) {
  const { showError } = useError();
  const { contentContainerStyle, bottomInset } = useLayout();
  const byName = useMemo(() => new Map(team.roster.map((p) => [p.name, p])), [team]);

  const initialXi = useMemo(
    () =>
      uniqueXi(
        team.starting_xi?.length ? team.starting_xi : team.roster.slice(0, 11).map((p) => p.name),
        team.roster
      ),
    [team]
  );

  const [xi, setXi] = useState<string[]>(initialXi);
  const [impactSub, setImpactSub] = useState<string>(team.impact_sub_name || '');
  const [picker, setPicker] = useState<{ slot: number } | null>(null);
  const [impactPickerOpen, setImpactPickerOpen] = useState(false);

  // Always start this tab scrolled to the top (showing the openers / top order),
  // not wherever a previous mount or a layout shift left it — the guided tour
  // opens this tab programmatically and it could otherwise land near the bottom
  // (Impact Sub / Autofill / Save).
  const scrollRef = useRef<ScrollView>(null);
  useEffect(() => {
    const id = requestAnimationFrame(() => scrollRef.current?.scrollTo({ y: 0, animated: false }));
    return () => cancelAnimationFrame(id);
  }, []);

  const setSlot = (slot: number, name: string) => {
    const next = [...xi];
    // Swap if the picked player is already in the XI elsewhere.
    const existingIdx = next.indexOf(name);
    if (existingIdx !== -1 && existingIdx !== slot) {
      next[existingIdx] = next[slot];
    }
    next[slot] = name;
    setXi(next);
  };

  const autofill = async () => {
    setSaveError(null);
    setSaving(true);
    try {
      await seasonApi.setPresets(careerId, { batting_order: [], starting_xi: null, impact_sub_name: null });
      await refresh();
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to autofill Starting XI');
      showError(err, { onRetry: autofill });
    } finally {
      setSaving(false);
    }
  };

  const save = async () => {
    const xiError = xiValidationError(xi, 'Starting XI', team.roster) || (competition === 'ipl' ? impactSubError(impactSub, xi, team.roster) : null);
    if (xiError) {
      setSaveError(xiError);
      return;
    }
    setSaveError(null);
    setSaving(true);
    try {
      await seasonApi.setPresets(careerId, {
        batting_order: xi,
        starting_xi: xi,
        impact_sub_name: competition === 'ipl' ? impactSub : null,
      });
      await refresh();
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save presets');
      showError(err, { onRetry: save });
    } finally {
      setSaving(false);
    }
  };

  const bench = benchNames(team.roster, xi);
  const impactSubOptions = bench.map((n) => {
    const p = byName.get(n);
    return { name: n, subtitle: p ? `${p.role} · OVR ${p.ovr}` : undefined };
  });

  return (
    <ScrollView ref={scrollRef} contentContainerStyle={[styles.content, contentContainerStyle, { paddingBottom: bottomInset }]} showsVerticalScrollIndicator={false}>
      <View>
        <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
          Starting XI
        </ThemedText>
        <ThemedText themeColor="textDim" style={styles.helpText}>
          This XI plays innings 1 if you bat first. Slot order is the batting order. Tap a slot to swap players.
        </ThemedText>
        <Card style={styles.lineupCard}>
          {xi.map((name, i) => {
            const slotNum = i + 1;
            const zone = ORDER_ZONES.find((z) => slotNum >= z.range[0] && slotNum <= z.range[1]);
            const player = byName.get(name);
            return (
              <View key={i}>
                {(i === 0 || ORDER_ZONES.find((z) => slotNum - 1 >= z.range[0] && slotNum - 1 <= z.range[1]) !== zone) && (
                  <ThemedText themeColor="textFaint" style={styles.zoneLabel}>
                    {zone?.label}
                  </ThemedText>
                )}
                {player ? (
                  <PlayerRow
                    player={player}
                    accentColor={accent}
                    onPress={() => setPicker({ slot: i })}
                    trailing={
                      <ThemedText themeColor="textFaint" style={styles.slotNum}>
                        #{slotNum}
                      </ThemedText>
                    }
                  />
                ) : (
                  <PlayerRow
                    player={{ name: 'Empty', role: '-', ovr: 0, batting_archetype: '', bowling_phase: '' }}
                    onPress={() => setPicker({ slot: i })}
                    subtitle="Tap to assign"
                  />
                )}
              </View>
            );
          })}
        </Card>
        <PlayerPickerModal
          visible={picker !== null}
          title="Starting XI"
          options={[...xi.filter(Boolean), ...bench].map((n) => {
            const p = byName.get(n);
            return { name: n, subtitle: p ? `${p.role} · OVR ${p.ovr}` : undefined };
          })}
          selected={picker ? xi[picker.slot] : undefined}
          onSelect={(name) => {
            if (picker) setSlot(picker.slot, name);
            setPicker(null);
          }}
          onClose={() => setPicker(null)}
        />
      </View>

      {competition === 'ipl' && (
        <View>
          <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
            Impact Sub
          </ThemedText>
          <ThemedText themeColor="textDim" style={styles.helpText}>
            If you bat first, your Impact Sub comes on for a batter at the innings break. If you bowl first, your
            Impact Sub starts the match in place of that batter and the original player returns at the break.
          </ThemedText>
          <Card style={styles.lineupCard}>
            {impactSub && byName.get(impactSub) ? (
              <PlayerRow player={byName.get(impactSub)!} accentColor={accent} onPress={() => setImpactPickerOpen(true)} />
            ) : (
              <PlayerRow
                player={{ name: 'Empty', role: '-', ovr: 0, batting_archetype: '', bowling_phase: '' }}
                onPress={() => setImpactPickerOpen(true)}
                subtitle="Tap to assign"
              />
            )}
          </Card>
          <PlayerPickerModal
            visible={impactPickerOpen}
            title="Impact Sub"
            options={impactSubOptions}
            selected={impactSub}
            onSelect={(name) => {
              setImpactSub(name);
              setImpactPickerOpen(false);
            }}
            onClose={() => setImpactPickerOpen(false)}
          />
        </View>
      )}

      <Button label="Autofill Starting XI" variant="secondary" accentColor={accent} onPress={autofill} />

      <Button
        label={saving ? 'Saving…' : 'Save Match Presets'}
        variant="primary"
        accentColor={accent}
        loading={saving}
        onPress={save}
      />
    </ScrollView>
  );
}

// ---------------------------------------------------------------------------
// Bowling Plan tab — 20-over default plan
// ---------------------------------------------------------------------------

function BowlingPlanTab({
  careerId,
  team,
  accent,
  saving,
  setSaving,
  setSaveError,
  refresh,
}: {
  careerId: string;
  team: NonNullable<ReturnType<typeof useLeague>['payload']>['teams'][number];
  accent?: string;
  saving: boolean;
  setSaving: (v: boolean) => void;
  setSaveError: (v: string | null) => void;
  refresh: () => Promise<void>;
}) {
  const { showError } = useError();
  const { contentContainerStyle, bottomInset } = useLayout();
  const byName = useMemo(() => new Map(team.roster.map((p) => [p.name, p])), [team]);
  const startingXi = useMemo(
    () =>
      uniqueXi(
        team.starting_xi?.length ? team.starting_xi : team.roster.slice(0, 11).map((p) => p.name),
        team.roster
      ),
    [team]
  );
  const eligibleBowlers = useMemo(() => {
    const names = [...startingXi, ...(team.impact_sub_name ? [team.impact_sub_name] : [])];
    return bowlingOptions(names, team.roster);
  }, [startingXi, team.impact_sub_name, team.roster]);

  const initialPlan = useMemo(() => {
    const saved = team.saved_bowling_order?.length ? team.saved_bowling_order : [];
    return Array.from({ length: 20 }, (_, i) => saved[i] ?? '');
  }, [team]);

  const [plan, setPlan] = useState<string[]>(initialPlan);
  const [pickerSlot, setPickerSlot] = useState<number | null>(null);

  const planError = bowlingPlanError(plan.filter(Boolean), 'Default bowling plan');
  const filledCount = plan.filter(Boolean).length;

  const save = async () => {
    // Either fully blank (auto) or all 20 filled — matches bowlingPlanError().
    if (filledCount !== 0 && filledCount !== 20) {
      setSaveError('Default bowling plan must contain all 20 overs, or be left completely blank.');
      return;
    }
    if (planError) {
      setSaveError(planError);
      return;
    }
    setSaveError(null);
    setSaving(true);
    try {
      await seasonApi.setPresets(careerId, { bowling_order: plan.filter(Boolean) });
      await refresh();
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save bowling plan');
      showError(err, { onRetry: save });
    } finally {
      setSaving(false);
    }
  };

  const overCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    plan.forEach((name) => {
      if (name) counts[name] = (counts[name] ?? 0) + 1;
    });
    return counts;
  }, [plan]);

  const autofill = () => {
    const names = [...startingXi, ...(team.impact_sub_name ? [team.impact_sub_name] : [])];
    const generated = autofillBowlingPlan(names, team.roster);
    setPlan(Array.from({ length: 20 }, (_, i) => generated[i] ?? ''));
  };

  return (
    <ScrollView contentContainerStyle={[styles.content, contentContainerStyle, { paddingBottom: bottomInset }]} showsVerticalScrollIndicator={false}>
      <ThemedText themeColor="textDim" style={styles.helpText}>
        Overs are grouped by phase — Powerplay (1-6), Middle (7-15), Death (16-20). Tap a slot to assign a bowler. Max
        4 overs each, never in consecutive overs. Leave fully blank for smart auto-pick.
      </ThemedText>

      <Button label="Auto-fill Best Lineup" variant="secondary" accentColor={accent} onPress={autofill} />

      {planError ? (
        <ThemedText themeColor="red" style={styles.helpText}>
          {planError}
        </ThemedText>
      ) : null}

      <Card style={styles.lineupCard}>
        {plan.map((name, i) => {
          const overNum = i + 1;
          const zone = OVER_PHASE_ZONES.find((z) => overNum >= z.range[0] && overNum <= z.range[1]);
          const prevZone = OVER_PHASE_ZONES.find((z) => overNum - 1 >= z.range[0] && overNum - 1 <= z.range[1]);
          const player = name ? byName.get(name) : undefined;
          return (
            <View key={i}>
              {(i === 0 || zone !== prevZone) && (
                <ThemedText themeColor="textFaint" style={styles.zoneLabel}>
                  {zone?.label}
                </ThemedText>
              )}
              {player ? (
                <PlayerRow
                  player={player}
                  accentColor={accent}
                  onPress={() => setPickerSlot(i)}
                  subtitle={`${player.role} · ${overCounts[name]}/4 overs`}
                  trailing={
                    <ThemedText themeColor="textFaint" style={styles.slotNum}>
                      Ov {overNum}
                    </ThemedText>
                  }
                />
              ) : (
                <PlayerRow
                  player={{ name: 'Empty', role: '-', ovr: 0, batting_archetype: '', bowling_phase: '' }}
                  onPress={() => setPickerSlot(i)}
                  subtitle="Tap to assign (auto-pick if blank)"
                  trailing={
                    <ThemedText themeColor="textFaint" style={styles.slotNum}>
                      Ov {overNum}
                    </ThemedText>
                  }
                />
              )}
            </View>
          );
        })}
      </Card>

      <PlayerPickerModal
        visible={pickerSlot !== null}
        title={`Over ${(pickerSlot ?? 0) + 1} Bowler`}
        allowClear
        options={eligibleBowlers.map((n) => {
          const p = byName.get(n);
          return { name: n, subtitle: p ? `${p.role} · Bowl ${p.bowl} · ${overCounts[n] ?? 0}/4 overs` : undefined };
        })}
        selected={pickerSlot !== null ? plan[pickerSlot] : undefined}
        onSelect={(name) => {
          if (pickerSlot !== null) {
            const next = [...plan];
            next[pickerSlot] = name;
            setPlan(next);
          }
          setPickerSlot(null);
        }}
        onClose={() => setPickerSlot(null)}
      />

      <Button
        label={saving ? 'Saving…' : 'Save Bowling Plan'}
        variant="primary"
        accentColor={accent}
        loading={saving}
        onPress={save}
      />
    </ScrollView>
  );
}

// ---------------------------------------------------------------------------
// Leadership tab — captain/vice/keeper
// ---------------------------------------------------------------------------

function LeadershipTab({
  careerId,
  team,
  accent,
  saving,
  setSaving,
  setSaveError,
  refresh,
}: {
  careerId: string;
  team: NonNullable<ReturnType<typeof useLeague>['payload']>['teams'][number];
  accent?: string;
  saving: boolean;
  setSaving: (v: boolean) => void;
  setSaveError: (v: string | null) => void;
  refresh: () => Promise<void>;
}) {
  const { showError } = useError();
  const { contentContainerStyle, bottomInset } = useLayout();
  const byName = useMemo(() => new Map(team.roster.map((p) => [p.name, p])), [team]);
  const keepers = useMemo(() => team.roster.filter((p) => p.role === 'Wicketkeeper'), [team]);

  const [captain, setCaptain] = useState(team.captain || team.roster[0]?.name || '');
  const [vice, setVice] = useState(team.vice_captain || team.roster[1]?.name || '');
  const [keeper, setKeeper] = useState(team.saved_wicketkeeper || keepers[0]?.name || '');

  const [picker, setPicker] = useState<'captain' | 'vice' | 'keeper' | null>(null);

  const rosterOptions = team.roster.map((p) => ({ name: p.name, subtitle: `${p.role} · OVR ${p.ovr}` }));
  const keeperOptions = keepers.length
    ? keepers.map((p) => ({ name: p.name, subtitle: `OVR ${p.ovr}` }))
    : [{ name: '', subtitle: 'No wicketkeeper drafted' }];

  const PICKER_CONFIG: Record<
    NonNullable<typeof picker>,
    { title: string; value: string; setValue: (v: string) => void; options: typeof rosterOptions }
  > = {
    captain: { title: 'Captain', value: captain, setValue: setCaptain, options: rosterOptions },
    vice: { title: 'Vice-Captain', value: vice, setValue: setVice, options: rosterOptions },
    keeper: { title: 'Wicketkeeper', value: keeper, setValue: setKeeper, options: keeperOptions },
  };

  const saveLeadership = async () => {
    setSaveError(null);
    setSaving(true);
    try {
      await seasonApi.setLeadership(careerId, {
        captain,
        vice,
        wicketkeeper: byName.get(keeper)?.role === 'Wicketkeeper' ? keeper : undefined,
      });
      await refresh();
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save leadership');
      showError(err, { onRetry: saveLeadership });
    } finally {
      setSaving(false);
    }
  };

  const renderField = (label: string, value: string, key: NonNullable<typeof picker>) => {
    const player = byName.get(value);
    return (
      <View style={styles.fieldRow}>
        <ThemedText themeColor="textDim" style={styles.fieldLabel}>
          {label}
        </ThemedText>
        <Pressable onPress={() => setPicker(key)}>
          <Card style={styles.fieldValueCard}>
            <ThemedText style={styles.fieldValue} numberOfLines={1}>
              {value || 'Select…'}
            </ThemedText>
            {player && (
              <ThemedText themeColor="textFaint" style={styles.fieldSub}>
                {player.role} · OVR {player.ovr}
              </ThemedText>
            )}
          </Card>
        </Pressable>
      </View>
    );
  };

  return (
    <ScrollView contentContainerStyle={[styles.content, contentContainerStyle, { paddingBottom: bottomInset }]} showsVerticalScrollIndicator={false}>
      <View>
        <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
          Leadership
        </ThemedText>
        {renderField('Captain', captain, 'captain')}
        {renderField('Vice-Captain', vice, 'vice')}
        {renderField('Wicketkeeper', keeper, 'keeper')}
        <Button
          label={saving ? 'Saving…' : 'Save Leadership'}
          variant="primary"
          accentColor={accent}
          loading={saving}
          onPress={saveLeadership}
        />
      </View>

      {picker && (
        <PlayerPickerModal
          visible
          title={PICKER_CONFIG[picker].title}
          options={PICKER_CONFIG[picker].options}
          selected={PICKER_CONFIG[picker].value}
          onSelect={(name) => {
            PICKER_CONFIG[picker].setValue(name);
            setPicker(null);
          }}
          onClose={() => setPicker(null)}
        />
      )}
    </ScrollView>
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
  segmentWrap: {
    paddingHorizontal: Spacing.three,
    paddingBottom: Spacing.two,
  },
  editNamesRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.three,
    paddingBottom: Spacing.two,
    gap: Spacing.two,
  },
  teamNameHeading: {
    flex: 1,
    fontSize: 16,
    fontWeight: '800',
  },
  editToggle: {
    fontSize: 13,
    fontWeight: '700',
  },
  rowPencil: {
    fontSize: 16,
    fontWeight: '700',
  },
  errorBanner: {
    marginHorizontal: Spacing.three,
    marginBottom: Spacing.two,
  },
  errorText: {
    fontSize: 12.5,
  },
  content: {
    padding: Spacing.three,
    paddingTop: 0,
    gap: Spacing.four,
    paddingBottom: ContentBottomInset,
  },
  rowBetween: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: Spacing.two,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  sortRow: {
    flexDirection: 'row',
    gap: 6,
  },
  sortPill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  rosterCard: {
    paddingBottom: 4,
  },
  helpText: {
    fontSize: 12,
    lineHeight: 18,
    marginBottom: Spacing.two,
  },
  lineupCard: {
    paddingBottom: 4,
    gap: 0,
  },
  zoneLabel: {
    fontSize: 10,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    paddingTop: Spacing.two,
    paddingBottom: 2,
  },
  slotNum: {
    fontSize: 11,
    fontWeight: '700',
  },
  fieldRow: {
    marginBottom: Spacing.two,
    gap: 4,
  },
  fieldLabel: {
    fontSize: 11.5,
    fontWeight: '600',
  },
  fieldValueCard: {
    paddingVertical: 10,
    paddingHorizontal: Spacing.three,
    borderRadius: Radius.sm,
  },
  fieldValue: {
    fontSize: 14,
    fontWeight: '700',
  },
  fieldSub: {
    fontSize: 11,
    marginTop: 2,
  },
});
