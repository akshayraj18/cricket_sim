import { useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from 'react-native';

import { liveMatchApi } from '@/api/liveMatch';
import { LiveMatchPayload, MatchCard, OverEvent, PlayerDict } from '@/api/types';
import { PlayerProfileSheet } from '@/components/player-profile-sheet';
import { PlayerRow } from '@/components/player-row';
import { ThemedText } from '@/components/themed-text';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Pill } from '@/components/ui/pill';
import { getTeamBackground, Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { abbreviateDismissal, abbreviateName } from '@/utils/names';
import {
  ORDER_ZONES,
  OVER_PHASE_ZONES,
  benchNames,
  bowlingOptions,
  bowlingPlanError,
  uniqueXi,
  xiValidationError,
} from '@/utils/lineup';

import { MatchScorecard } from './match-scorecard';
import { PlayerPickerModal } from './player-picker-modal';

export function LiveMatchHub({
  careerId,
  match,
  accent,
  onChange,
  onComplete,
}: {
  careerId: string;
  match: LiveMatchPayload;
  accent?: string;
  /** Called with the refreshed match payload after any action. */
  onChange: (match: LiveMatchPayload) => void;
  /** Called once the match is acknowledged complete; caller should refresh the league payload. */
  onComplete: () => void;
}) {
  const theme = useTheme();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wrap = async (fn: () => Promise<LiveMatchPayload>) => {
    setBusy(true);
    setError(null);
    try {
      const next = await fn();
      onChange(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setBusy(false);
    }
  };

  const completeMatch = async () => {
    setBusy(true);
    setError(null);
    try {
      await liveMatchApi.complete(careerId);
      onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to complete match');
      setBusy(false);
    }
  };

  return (
    <View style={styles.container}>
      {error && (
        <ThemedText themeColor="red" style={styles.errorText}>
          {error}
        </ThemedText>
      )}
      {busy && (
        <View style={styles.busyOverlay}>
          <ActivityIndicator color={theme.green} />
        </View>
      )}

      {match.status === 'toss' && <TossStage match={match} accent={accent} wrap={wrap} careerId={careerId} />}

      {(match.status === 'lineup' || match.status === 'batting_order') && (
        <LineupStage match={match} accent={accent} wrap={wrap} careerId={careerId} />
      )}

      {match.status === 'impact' && <ImpactStage match={match} accent={accent} wrap={wrap} careerId={careerId} />}

      {match.status === 'super_over_setup' && (
        <SuperOverStage match={match} accent={accent} wrap={wrap} careerId={careerId} />
      )}

      {match.status === 'next_batter' && (
        <NextBatterStage match={match} accent={accent} wrap={wrap} careerId={careerId} />
      )}

      {match.status === 'complete' && (
        <FinalScorecardStage match={match} onComplete={completeMatch} canComplete />
      )}

      {!['toss', 'lineup', 'batting_order', 'impact', 'super_over_setup', 'next_batter', 'complete'].includes(
        match.status
      ) && <OverHubStage match={match} accent={accent} wrap={wrap} careerId={careerId} />}
    </View>
  );
}

// ---------------------------------------------------------------------------
// Toss
// ---------------------------------------------------------------------------

function TossStage({
  match,
  accent,
  wrap,
  careerId,
}: {
  match: LiveMatchPayload;
  accent?: string;
  wrap: (fn: () => Promise<LiveMatchPayload>) => Promise<void>;
  careerId: string;
}) {
  const theme = useTheme();
  return (
    <View style={styles.stage}>
      <View style={[styles.scoreboard, { backgroundColor: accent ?? theme.green }]}>
        <ThemedText style={styles.scoreboardSmall}>
          {match.team1} vs {match.team2}
        </ThemedText>
        <ThemedText style={styles.scoreboardLine}>Toss</ThemedText>
        <ThemedText style={styles.scoreboardMessage}>{match.message}</ThemedText>
      </View>
      <Card>
        <ThemedText style={styles.panelTitle}>Choose Decision</ThemedText>
        <ThemedText themeColor="textDim" style={styles.helpText}>
          Bat first uses your saved Batting First XI. Bowl first uses your saved Bowling First XI and any saved
          20-over bowling plan.
        </ThemedText>
        <View style={styles.buttonRow}>
          <Button
            label="Bat First"
            variant="primary"
            accentColor={accent}
            onPress={() => wrap(() => liveMatchApi.toss(careerId, { decision: 'bat' }))}
          />
          <Button
            label="Bowl First"
            variant="primary"
            accentColor={accent}
            onPress={() => wrap(() => liveMatchApi.toss(careerId, { decision: 'bowl' }))}
          />
        </View>
      </Card>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Lineup hub — confirm Batting/Bowling First XI + (if bowling) 20-over plan
// ---------------------------------------------------------------------------

function LineupStage({
  match,
  accent,
  wrap,
  careerId,
}: {
  match: LiveMatchPayload;
  accent?: string;
  wrap: (fn: () => Promise<LiveMatchPayload>) => Promise<void>;
  careerId: string;
}) {
  const theme = useTheme();
  const isBowling = match.lineup_context === 'bowling';
  const context = 'Starting XI';
  const suggested = match.suggested;
  const byName = useMemo(() => new Map(suggested.map((p) => [p.name, p])), [suggested]);

  const initialXi = useMemo(
    () => uniqueXi(match.lineup_xi, suggested),
    [match.lineup_xi, suggested]
  );
  const [xi, setXi] = useState<string[]>(initialXi);
  const [plan, setPlan] = useState<string[]>(
    Array.from({ length: 20 }, (_, i) => match.saved_bowling_order?.[i] ?? '')
  );
  const [picker, setPicker] = useState<{ kind: 'xi' | 'plan'; slot: number } | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const eligibleBowlers = useMemo(() => bowlingOptions(xi, suggested), [xi, suggested]);
  const overCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    plan.forEach((name) => {
      if (name) counts[name] = (counts[name] ?? 0) + 1;
    });
    return counts;
  }, [plan]);

  const setXiSlot = (slot: number, name: string) => {
    const next = [...xi];
    const existingIdx = next.indexOf(name);
    if (existingIdx !== -1 && existingIdx !== slot) next[existingIdx] = next[slot];
    next[slot] = name;
    setXi(next);
  };

  const confirm = async () => {
    const xiError = xiValidationError(xi, context, suggested);
    const filledCount = plan.filter(Boolean).length;
    const planError = isBowling
      ? filledCount !== 0 && filledCount !== 20
        ? 'Live bowling plan must contain all 20 overs, or be left completely blank.'
        : bowlingPlanError(plan.filter(Boolean), 'Live bowling plan')
      : '';
    const err = xiError || planError;
    if (err) {
      setValidationError(err);
      return;
    }
    setValidationError(null);
    await wrap(() =>
      liveMatchApi.setLineup(careerId, {
        xi,
        batting_order: isBowling ? [] : xi,
        bowling_order: isBowling ? plan.filter(Boolean) : [],
        intents: {},
        save: false,
        context: isBowling ? 'bowling' : 'batting',
        wicketkeeper: match.saved_wicketkeeper || '',
      })
    );
  };

  const bench = benchNames(suggested, xi);

  return (
    <View style={styles.stage}>
      <Card>
        <View style={styles.rowBetween}>
          <ThemedText style={styles.panelTitle}>{context}</ThemedText>
        </View>
        <ThemedText themeColor="textDim" style={styles.helpText}>
          {match.message} Tap a slot to assign or swap a player. Slots are grouped by where each player naturally
          bats — openers, middle order, death overs, tail.
        </ThemedText>
        {match.swap_notice ? (
          <View style={[styles.noticeBanner, { borderColor: accent ?? theme.green }]}>
            <ThemedText themeColor="text" style={styles.helpText}>
              {match.swap_notice}
            </ThemedText>
          </View>
        ) : null}
        {validationError && (
          <ThemedText themeColor="red" style={styles.helpText}>
            {validationError}
          </ThemedText>
        )}
        {xi.map((name, i) => {
          const slotNum = i + 1;
          const zone = ORDER_ZONES.find((z) => slotNum >= z.range[0] && slotNum <= z.range[1]);
          const prevZone = ORDER_ZONES.find((z) => slotNum - 1 >= z.range[0] && slotNum - 1 <= z.range[1]);
          const player = byName.get(name);
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
                  onPress={() => setPicker({ kind: 'xi', slot: i })}
                  trailing={
                    <ThemedText themeColor="textFaint" style={styles.slotNum}>
                      #{slotNum}
                    </ThemedText>
                  }
                />
              ) : (
                <PlayerRow
                  player={{ name: 'Empty', role: '-', ovr: 0, batting_archetype: '', bowling_phase: '' }}
                  onPress={() => setPicker({ kind: 'xi', slot: i })}
                  subtitle="Tap to assign"
                />
              )}
            </View>
          );
        })}
      </Card>

      {isBowling && (
        <Card>
          <ThemedText style={styles.panelTitle}>20-Over Bowling Plan</ThemedText>
          <ThemedText themeColor="textDim" style={styles.helpText}>
            Grouped by phase — Powerplay (1-6), Middle (7-15), Death (16-20). Max 4 overs each, never in consecutive
            overs. Leave fully blank for smart auto-pick.
          </ThemedText>
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
                    onPress={() => setPicker({ kind: 'plan', slot: i })}
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
                    onPress={() => setPicker({ kind: 'plan', slot: i })}
                    subtitle="Auto-pick if blank"
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
      )}

      <Button label="Confirm XI" variant="primary" accentColor={accent} onPress={confirm} />

      <PlayerPickerModal
        visible={picker?.kind === 'xi'}
        title={context}
        options={[...xi.filter(Boolean), ...bench].map((n) => {
          const p = byName.get(n);
          return { name: n, subtitle: p ? `${p.role} · OVR ${p.ovr}` : undefined };
        })}
        selected={picker ? xi[picker.slot] : undefined}
        onSelect={(name) => {
          if (picker) setXiSlot(picker.slot, name);
          setPicker(null);
        }}
        onClose={() => setPicker(null)}
      />

      <PlayerPickerModal
        visible={picker?.kind === 'plan'}
        title={`Over ${(picker?.slot ?? 0) + 1} Bowler`}
        allowClear
        options={eligibleBowlers.map((n) => {
          const p = byName.get(n);
          return { name: n, subtitle: p ? `${p.role} · Bowl ${p.bowl} · ${overCounts[n] ?? 0}/4 overs` : undefined };
        })}
        selected={picker ? plan[picker.slot] : undefined}
        onSelect={(name) => {
          if (picker) {
            const next = [...plan];
            next[picker.slot] = name;
            setPlan(next);
          }
          setPicker(null);
        }}
        onClose={() => setPicker(null)}
      />
    </View>
  );
}

// ---------------------------------------------------------------------------
// Impact sub hub — innings break
// ---------------------------------------------------------------------------

function ImpactStage({
  match,
  accent,
  wrap,
  careerId,
}: {
  match: LiveMatchPayload;
  accent?: string;
  wrap: (fn: () => Promise<LiveMatchPayload>) => Promise<void>;
  careerId: string;
}) {
  const theme = useTheme();
  const impact = match.impact;
  const first = match.innings?.[0];
  const presetOut = impact?.default_out && impact?.xi.some((p) => p.name === impact.default_out) ? impact.default_out : '';
  const presetIn = impact?.default_in && impact?.bench.some((p) => p.name === impact.default_in) ? impact.default_in : '';
  const [outName, setOutName] = useState(presetOut || impact?.xi[0]?.name || '');
  const [inName, setInName] = useState(presetIn || impact?.bench[0]?.name || '');
  const [pickerKind, setPickerKind] = useState<'out' | 'in' | null>(null);

  if (!impact) return null;

  const outPlayer = impact.xi.find((p) => p.name === outName);
  const inPlayer = impact.bench.find((p) => p.name === inName);

  return (
    <View style={styles.stage}>
      {first && (
        <Card>
          <ThemedText style={styles.panelTitle}>
            {first.team} {first.score}
          </ThemedText>
          <ThemedText themeColor="textDim" style={styles.helpText}>
            Chase target: {Number(first.score.split('/')[0]) + 1}
          </ThemedText>
          <MiniInningsCards innings={first} />
        </Card>
      )}

      <View style={[styles.scoreboard, { backgroundColor: accent ?? theme.green }]}>
        <ThemedText style={styles.scoreboardSmall}>Innings Break</ThemedText>
        <ThemedText style={styles.scoreboardLine}>Impact Sub</ThemedText>
        <ThemedText style={styles.scoreboardMessage}>{match.message}</ThemedText>
      </View>

      <Card>
        <ThemedText style={styles.panelTitle}>Substitution Desk</ThemedText>
        <ThemedText themeColor="textDim" style={styles.helpText}>
          Your saved Impact Sub is preselected — pick a different XI player to remove or bench player to bring on if
          you&apos;d rather.
        </ThemedText>
        <ThemedText themeColor="textFaint" style={styles.fieldLabel}>
          Out
        </ThemedText>
        {outPlayer && (
          <PlayerRow player={outPlayer} accentColor={accent} onPress={() => setPickerKind('out')} />
        )}
        <ThemedText themeColor="textFaint" style={[styles.fieldLabel, { marginTop: Spacing.two }]}>
          In
        </ThemedText>
        {inPlayer && <PlayerRow player={inPlayer} accentColor={accent} onPress={() => setPickerKind('in')} />}
        <View style={styles.buttonRow}>
          <Button
            label="Use Impact Sub"
            variant="primary"
            accentColor={accent}
            onPress={() => wrap(() => liveMatchApi.applyImpactSub(careerId, { out: outName, in: inName }))}
          />
          <Button label="Skip" variant="secondary" onPress={() => wrap(() => liveMatchApi.applyImpactSub(careerId, {}))} />
        </View>
      </Card>

      <PlayerPickerModal
        visible={pickerKind === 'out'}
        title="Player coming off"
        options={impact.xi.map((p) => ({ name: p.name, subtitle: `${p.role} · Bat ${p.bat}/Bowl ${p.bowl}` }))}
        selected={outName}
        onSelect={(name) => {
          setOutName(name);
          setPickerKind(null);
        }}
        onClose={() => setPickerKind(null)}
      />
      <PlayerPickerModal
        visible={pickerKind === 'in'}
        title="Player coming on"
        options={impact.bench.map((p) => ({ name: p.name, subtitle: `${p.role} · Bat ${p.bat}/Bowl ${p.bowl}` }))}
        selected={inName}
        onSelect={(name) => {
          setInName(name);
          setPickerKind(null);
        }}
        onClose={() => setPickerKind(null)}
      />
    </View>
  );
}

// ---------------------------------------------------------------------------
// Super Over setup
// ---------------------------------------------------------------------------

function SuperOverStage({
  match,
  accent,
  wrap,
  careerId,
}: {
  match: LiveMatchPayload;
  accent?: string;
  wrap: (fn: () => Promise<LiveMatchPayload>) => Promise<void>;
  careerId: string;
}) {
  const theme = useTheme();
  const so = match.super_over as import('@/api/types').SuperOverSetupPayload | null;
  const topBatters = (so?.batters ?? []).slice(0, 8);
  const bowlers = so?.bowlers ?? [];
  const [selectedBatters, setSelectedBatters] = useState<string[]>(topBatters.slice(0, 3).map((p) => p.name));
  const [bowler, setBowler] = useState(bowlers[0]?.name ?? '');

  if (!so) return null;

  const toggleBatter = (name: string) => {
    setSelectedBatters((prev) => {
      if (prev.includes(name)) return prev.filter((n) => n !== name);
      if (prev.length >= 3) return prev;
      return [...prev, name];
    });
  };

  return (
    <View style={styles.stage}>
      <View style={[styles.scoreboard, { backgroundColor: accent ?? theme.green }]}>
        <ThemedText style={styles.scoreboardSmall}>Tied Match</ThemedText>
        <ThemedText style={styles.scoreboardLine}>Super Over</ThemedText>
        <ThemedText style={styles.scoreboardMessage}>{so.message || match.message}</ThemedText>
        <ThemedText style={styles.scoreboardSmall}>
          {so.batting_first} bat first. {so.batting_second} chase.
        </ThemedText>
      </View>

      <Card>
        <View style={styles.rowBetween}>
          <ThemedText style={styles.panelTitle}>Pick Super Over Unit</ThemedText>
        </View>
        <ThemedText themeColor="textDim" style={styles.helpText}>
          Choose exactly 3 batters. First two start at the crease; the over ends after six balls or two wickets.
        </ThemedText>
        {topBatters.map((p) => {
          const active = selectedBatters.includes(p.name);
          return (
            <Pressable
              key={p.name}
              onPress={() => toggleBatter(p.name)}
              style={[styles.choiceRow, { borderColor: theme.border }, active && { backgroundColor: theme.bgElevated }]}>
              <View style={[styles.checkbox, { borderColor: accent ?? theme.green }, active && { backgroundColor: accent ?? theme.green }]}>
                {active && <ThemedText style={styles.checkboxMark}>✓</ThemedText>}
              </View>
              <View style={styles.flex1}>
                <ThemedText style={styles.choiceName}>{p.name}</ThemedText>
                <ThemedText themeColor="textDim" style={styles.choiceSub}>
                  Bat {p.bat} · {p.batting_archetype} · Form {p.form}
                </ThemedText>
              </View>
            </Pressable>
          );
        })}

        <ThemedText style={[styles.panelTitle, { marginTop: Spacing.three }]}>Bowler</ThemedText>
        {bowlers.map((p) => {
          const active = bowler === p.name;
          return (
            <Pressable
              key={p.name}
              onPress={() => setBowler(p.name)}
              style={[styles.choiceRow, { borderColor: theme.border }, active && { backgroundColor: theme.bgElevated }]}>
              <View style={[styles.radio, { borderColor: accent ?? theme.green }]}>
                {active && <View style={[styles.radioDot, { backgroundColor: accent ?? theme.green }]} />}
              </View>
              <View style={styles.flex1}>
                <ThemedText style={styles.choiceName}>{p.name}</ThemedText>
                <ThemedText themeColor="textDim" style={styles.choiceSub}>
                  Bowl {p.bowl} · {p.bowling_phase}
                </ThemedText>
              </View>
            </Pressable>
          );
        })}

        <Button
          label="Play Super Over"
          variant="primary"
          accentColor={accent}
          disabled={selectedBatters.length !== 3 || !bowler}
          onPress={() =>
            wrap(() => liveMatchApi.setSuperOverLineup(careerId, { batters: selectedBatters, bowler }))
          }
        />
      </Card>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Next batter hub
// ---------------------------------------------------------------------------

function NextBatterStage({
  match,
  accent,
  wrap,
  careerId,
}: {
  match: LiveMatchPayload;
  accent?: string;
  wrap: (fn: () => Promise<LiveMatchPayload>) => Promise<void>;
  careerId: string;
}) {
  const theme = useTheme();
  const score = match.score;
  if (!score) return null;
  const wicket = score.last_wicket;
  const batter = wicket?.batter ?? '';
  const howOut = wicket?.description || 'Wicket';

  return (
    <View style={styles.stage}>
      <Scoreboard match={match} accent={accent} />
      <Card>
        <ThemedText style={styles.panelTitle}>Batting Card</ThemedText>
        <BattingCardTable bats={score.bat_stats} score={score} />
      </Card>
      <Card>
        <ThemedText style={styles.panelTitle}>{batter || 'Batter'} is out!</ThemedText>
        <ThemedText themeColor="textDim" style={styles.helpText}>
          {howOut}{'\n'}Choose who comes in next.
        </ThemedText>
        {score.next_batter_options.map((p) => (
          <Pressable
            key={p.name}
            onPress={() => wrap(() => liveMatchApi.selectNextBatter(careerId, { name: p.name }))}
            style={[styles.choiceRow, { borderColor: theme.border }]}>
            <View style={styles.flex1}>
              <ThemedText style={styles.choiceName}>{p.name}</ThemedText>
              <ThemedText themeColor="textDim" style={styles.choiceSub}>
                {p.preferred_position ? `${p.preferred_position} · ` : ''}
                {p.role} · Bat {p.bat} / Bowl {p.bowl} · Form {p.form}
              </ThemedText>
            </View>
          </Pressable>
        ))}
      </Card>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Over hub — main ball-by-ball control screen
// ---------------------------------------------------------------------------

function OverHubStage({
  match,
  accent,
  wrap,
  careerId,
}: {
  match: LiveMatchPayload;
  accent?: string;
  wrap: (fn: () => Promise<LiveMatchPayload>) => Promise<void>;
  careerId: string;
}) {
  const theme = useTheme();
  const score = match.score;
  const [profilePlayer, setProfilePlayer] = useState<PlayerDict | null>(null);
  const [strikerAgg, setStrikerAgg] = useState(score?.striker_aggression ?? 3);
  const [nonStrikerAgg, setNonStrikerAgg] = useState(score?.non_striker_aggression ?? 3);
  const [bowlerAgg, setBowlerAgg] = useState(score?.bowler_aggression ?? 2);

  if (!score) return null;

  const applyAggression = async () => {
    const batting: Record<string, number> = {};
    if (score.user_batting) {
      batting[score.striker] = strikerAgg;
      batting[score.non_striker] = nonStrikerAgg;
    }
    const bowling: Record<string, number> = {};
    if (score.user_bowling && score.active_bowler) {
      bowling[score.active_bowler] = bowlerAgg;
    }
    await liveMatchApi.setAggression(careerId, { batting, bowling });
  };

  const runAction = (fn: () => Promise<LiveMatchPayload>) =>
    wrap(async () => {
      await applyAggression();
      return fn();
    });

  return (
    <View style={styles.stage}>
      <Scoreboard match={match} accent={accent} />

      <Card>
        <ThemedText style={styles.panelTitle}>Ball Controls</ThemedText>
        <ThemedText themeColor="textDim" style={styles.helpText}>
          {score.user_batting
            ? 'Set aggression for both batters, then play one ball, one over, or simulate a longer stretch.'
            : 'Set bowling aggression and choose a bowler when needed. If no bowler is active, pick one from the list below.'}
        </ThemedText>

        {score.user_batting && (
          <>
            <AggressionSlider label={`${score.striker} (striker) aggression`} value={strikerAgg} onChange={setStrikerAgg} accent={accent} />
            <AggressionSlider label={`${score.non_striker} aggression`} value={nonStrikerAgg} onChange={setNonStrikerAgg} accent={accent} />
          </>
        )}
        {score.user_bowling && (
          <AggressionSlider
            label="Bowling aggression"
            value={bowlerAgg}
            onChange={setBowlerAgg}
            accent={accent}
            disabled={!score.active_bowler}
            min={1}
            max={5}
            lowLabel="contain"
            highLabel="attack"
          />
        )}

        <View style={styles.buttonRow}>
          <Button label="Next Ball" variant="primary" accentColor={accent} onPress={() => runAction(() => liveMatchApi.playBall(careerId, {}))} />
          <Button label="Next Over" variant="secondary" onPress={() => runAction(() => liveMatchApi.playOver(careerId, {}))} />
        </View>
        <View style={styles.buttonRow}>
          <Button label="Skip 5 Overs" variant="ghost" accentColor={accent} small onPress={() => runAction(() => liveMatchApi.playUntil(careerId, { balls: 30, stop_on_wicket: false }))} />
          <Button label="Skip 10 Overs" variant="ghost" accentColor={accent} small onPress={() => runAction(() => liveMatchApi.playUntil(careerId, { balls: 60, stop_on_wicket: false }))} />
          <Button label="End Innings" variant="ghost" accentColor={accent} small onPress={() => runAction(() => liveMatchApi.playUntil(careerId, { balls: 120, stop_on_wicket: false }))} />
        </View>
      </Card>

      <Card>
        <ThemedText style={styles.panelTitle}>{score.user_bowling ? 'Choose Bowler' : 'Bowler Queue'}</ThemedText>
        {match.available_bowlers.map((p) => {
          const disabled = !(score.user_bowling && (!score.active_bowler || score.active_bowler === p.name));
          return (
            <Pressable
              key={p.name}
              disabled={disabled}
              onPress={() => runAction(() => liveMatchApi.playBall(careerId, { bowler: p.name }))}
              style={[styles.choiceRow, { borderColor: theme.border }, disabled && styles.choiceDisabled]}>
              <View style={styles.flex1}>
                <ThemedText style={styles.choiceName}>{p.name}</ThemedText>
                <ThemedText themeColor="textDim" style={styles.choiceSub}>
                  Bowl {p.bowl} · Match {p.match_overs}-{p.match_wickets}, Econ {p.match_econ} · {p.bowling_phase}
                </ThemedText>
              </View>
            </Pressable>
          );
        })}
      </Card>

      <Card>
        <ThemedText style={styles.panelTitle}>Batting Card</ThemedText>
        <BattingCardTable bats={score.bat_stats} score={score} onPlayerPress={setProfilePlayer} />
      </Card>
      <Card>
        <ThemedText style={styles.panelTitle}>Bowling Card</ThemedText>
        <BowlingCardTable bowls={score.bowl_stats} onPlayerPress={setProfilePlayer} />
      </Card>

      <Card>
        <ThemedText style={styles.panelTitle}>Recent Overs</ThemedText>
        {score.over_log.length === 0 && (
          <ThemedText themeColor="textDim" style={styles.helpText}>
            No overs bowled yet.
          </ThemedText>
        )}
        {score.over_log.map((o, i) => (
          <View key={i} style={styles.overLogRow}>
            <ThemedText style={styles.overLogTitle}>
              Over {o.over}: {o.bowler}
            </ThemedText>
            <View style={styles.overLogBalls}>
              {o.events.map((e, j) => (
                <BallChip key={j} event={e} accent={accent} />
              ))}
            </View>
            {o.events
              .filter((e) => e.kind === 'wicket')
              .map((e, j) => (
                <ThemedText key={j} themeColor="red" style={styles.wicketNote}>
                  {e.description}
                </ThemedText>
              ))}
          </View>
        ))}
      </Card>

      <PlayerProfileSheet player={profilePlayer} onClose={() => setProfilePlayer(null)} accentColor={accent} />
    </View>
  );
}

// ---------------------------------------------------------------------------
// Final scorecard
// ---------------------------------------------------------------------------

export function FinalScorecardStage({
  match,
  card: cardOverride,
  onComplete,
  canComplete,
  accent,
}: {
  match?: LiveMatchPayload;
  card?: MatchCard;
  onComplete?: () => void;
  canComplete: boolean;
  accent?: string;
}) {
  const card = cardOverride ?? match?.card;
  if (!card) return null;
  return <MatchScorecard card={card} onComplete={onComplete} canComplete={canComplete} accent={accent} />;
}

// ---------------------------------------------------------------------------
// Shared sub-components
// ---------------------------------------------------------------------------

function Scoreboard({ match, accent }: { match: LiveMatchPayload; accent?: string }) {
  const theme = useTheme();
  const score = match.score;
  if (!score) return null;
  const overs = `${Math.floor(score.balls / 6)}.${score.balls % 6}`;
  const striker = score.bat_stats.find((p) => p.name === score.striker);
  const nonStriker = score.bat_stats.find((p) => p.name === score.non_striker);
  const bowler = score.bowl_stats.find((p) => p.name === score.active_bowler);
  const neededRuns = score.target ? Math.max(0, score.target - score.runs) : 0;
  const ballsLeft = Math.max(0, 120 - score.balls);

  return (
    <View style={[styles.scoreboard, { backgroundColor: getTeamBackground(score.batting_team) }]}>
      <ThemedText style={styles.scoreboardTeam} numberOfLines={1}>
        {score.batting_team}
      </ThemedText>
      <View style={styles.scoreboardScoreRow}>
        <ThemedText style={styles.scoreboardLine}>
          {score.runs}/{score.wickets}
        </ThemedText>
        <ThemedText style={styles.scoreboardOvers}>({overs} ov)</ThemedText>
      </View>
      {score.target ? (
        <ThemedText style={styles.scoreboardSmall}>Target {score.target}</ThemedText>
      ) : null}

      {score.striker ? (
        <View style={styles.batterLine}>
          <ThemedText style={styles.strikeMark}>{'>'}</ThemedText>
          <ThemedText style={styles.batterName} numberOfLines={1}>
            {score.striker}
          </ThemedText>
          <ThemedText style={styles.batterFigs}>
            {striker?.runs ?? 0} ({striker?.balls ?? 0})
          </ThemedText>
        </View>
      ) : null}
      {score.non_striker ? (
        <View style={styles.batterLine}>
          <ThemedText style={styles.strikeMark}> </ThemedText>
          <ThemedText style={styles.batterName} numberOfLines={1}>
            {score.non_striker}
          </ThemedText>
          <ThemedText style={styles.batterFigs}>
            {nonStriker?.runs ?? 0} ({nonStriker?.balls ?? 0})
          </ThemedText>
        </View>
      ) : null}

      {score.partnership ? (
        <View style={styles.scoreboardDivider}>
          <ThemedText style={styles.scoreboardSmall}>Partnership</ThemedText>
          <ThemedText style={[styles.scoreboardSmall, styles.scoreboardSmallStrong]}>{score.partnership}</ThemedText>
        </View>
      ) : null}

      <View style={styles.currentOverBlock}>
        <ThemedText style={styles.scoreboardSmall} numberOfLines={1}>
          {abbreviateName(score.active_bowler ?? 'No bowler')}
          {bowler ? ` · ${bowler.wickets ?? 0}-${bowler.runs ?? 0} (${bowler.overs})` : ''}
        </ThemedText>
        <View style={styles.overLogBalls}>
          {score.current_over.map((e, i) => (
            <BallChip key={i} event={e} accent={theme.bgCard} />
          ))}
        </View>
      </View>

      <ThemedText style={styles.scoreboardSmall}>
        {score.phase}
        {score.target ? ` · ${neededRuns} needed off ${ballsLeft}` : ` · ${ballsLeft} balls left`}
      </ThemedText>
    </View>
  );
}

function BallChip({ event, accent }: { event: OverEvent; accent?: string }) {
  const theme = useTheme();
  const isWicket = event.kind === 'wicket';
  return (
    <View
      style={[
        styles.ballChip,
        { backgroundColor: isWicket ? theme.red : (accent ?? theme.badgeBg), borderColor: theme.border },
      ]}>
      <ThemedText style={[styles.ballChipText, isWicket && { color: '#fff' }]}>{event.label}</ThemedText>
    </View>
  );
}

function MiniInningsCards({ innings }: { innings: { full_batting?: { name: string; runs: number; balls: number }[]; batting: { name: string; runs: number; balls: number }[]; full_bowling?: { name: string; wickets: number; runs: number }[]; bowling: { name: string; wickets: number; runs: number }[] } }) {
  const batters = (innings.full_batting ?? innings.batting).slice(0, 4);
  const bowlers = (innings.full_bowling ?? innings.bowling).slice(0, 4);
  return (
    <View style={styles.miniGrid}>
      <View style={styles.flex1}>
        <Pill label="Batters" />
        {batters.map((b) => (
          <View key={b.name} style={styles.miniRow}>
            <ThemedText themeColor="textDim" style={styles.miniName} numberOfLines={1}>
              {abbreviateName(b.name)}
            </ThemedText>
            <ThemedText style={styles.miniValue}>
              {b.runs} ({b.balls})
            </ThemedText>
          </View>
        ))}
      </View>
      <View style={styles.flex1}>
        <Pill label="Bowlers" />
        {bowlers.map((b) => (
          <View key={b.name} style={styles.miniRow}>
            <ThemedText themeColor="textDim" style={styles.miniName} numberOfLines={1}>
              {abbreviateName(b.name)}
            </ThemedText>
            <ThemedText style={styles.miniValue}>
              {b.wickets}/{b.runs}
            </ThemedText>
          </View>
        ))}
      </View>
    </View>
  );
}

export function BattingCardTable({
  bats,
  score,
  onPlayerPress,
}: {
  bats: { name: string; dismissal?: string; runs: number; balls: number; fours: number; sixes: number }[];
  score?: { striker?: string; non_striker?: string };
  onPlayerPress?: (player: PlayerDict) => void;
}) {
  const theme = useTheme();
  if (!bats.length) {
    return (
      <ThemedText themeColor="textDim" style={styles.helpText}>
        No batters yet.
      </ThemedText>
    );
  }
  return (
    <View>
      <View style={styles.tableHeaderRow}>
        <ThemedText themeColor="textFaint" style={[styles.tableHeaderCell, styles.tableNameCol]}>
          Batter
        </ThemedText>
        <ThemedText themeColor="textFaint" style={styles.tableHeaderCell}>
          R
        </ThemedText>
        <ThemedText themeColor="textFaint" style={styles.tableHeaderCell}>
          B
        </ThemedText>
        <ThemedText themeColor="textFaint" style={styles.tableHeaderCell}>
          4s
        </ThemedText>
        <ThemedText themeColor="textFaint" style={styles.tableHeaderCell}>
          6s
        </ThemedText>
        <ThemedText themeColor="textFaint" style={styles.tableHeaderCell}>
          SR
        </ThemedText>
      </View>
      {bats.map((b) => {
        const sr = b.balls ? ((b.runs / b.balls) * 100).toFixed(1) : '0.0';
        const isOnStrike = score && b.name === score.striker;
        const isAtCrease = score && (b.name === score.striker || b.name === score.non_striker);
        return (
          <View key={b.name} style={[styles.tableRow, { borderBottomColor: theme.border }]}>
            <View style={styles.tableNameCol}>
              <ThemedText style={styles.tableName} numberOfLines={1}>
                {isOnStrike ? '> ' : ''}
                {abbreviateName(b.name)}
                {isAtCrease ? '*' : ''}
              </ThemedText>
              {b.dismissal ? (
                <ThemedText themeColor="textFaint" style={styles.tableDismissal} numberOfLines={1}>
                  {abbreviateDismissal(b.dismissal)}
                </ThemedText>
              ) : isAtCrease ? (
                <ThemedText themeColor="green" style={styles.tableDismissal}>
                  not out
                </ThemedText>
              ) : null}
            </View>
            <ThemedText style={styles.tableCell}>{b.runs}</ThemedText>
            <ThemedText style={styles.tableCell}>{b.balls}</ThemedText>
            <ThemedText style={styles.tableCell}>{b.fours}</ThemedText>
            <ThemedText style={styles.tableCell}>{b.sixes}</ThemedText>
            <ThemedText style={styles.tableCell}>{sr}</ThemedText>
          </View>
        );
      })}
    </View>
  );
}

export function BowlingCardTable({
  bowls,
  onPlayerPress,
}: {
  bowls: { name: string; overs: string; runs: number; wickets: number; maidens: number; econ: number }[];
  onPlayerPress?: (player: PlayerDict) => void;
}) {
  const theme = useTheme();
  if (!bowls.length) {
    return (
      <ThemedText themeColor="textDim" style={styles.helpText}>
        No bowling yet.
      </ThemedText>
    );
  }
  return (
    <View>
      <View style={styles.tableHeaderRow}>
        <ThemedText themeColor="textFaint" style={[styles.tableHeaderCell, styles.tableNameCol]}>
          Bowler
        </ThemedText>
        <ThemedText themeColor="textFaint" style={styles.tableHeaderCell}>
          O
        </ThemedText>
        <ThemedText themeColor="textFaint" style={styles.tableHeaderCell}>
          M
        </ThemedText>
        <ThemedText themeColor="textFaint" style={styles.tableHeaderCell}>
          R
        </ThemedText>
        <ThemedText themeColor="textFaint" style={styles.tableHeaderCell}>
          W
        </ThemedText>
        <ThemedText themeColor="textFaint" style={styles.tableHeaderCell}>
          Econ
        </ThemedText>
      </View>
      {bowls.map((b) => (
        <View key={b.name} style={[styles.tableRow, { borderBottomColor: theme.border }]}>
          <ThemedText style={[styles.tableName, styles.tableNameCol]} numberOfLines={1}>
            {abbreviateName(b.name)}
          </ThemedText>
          <ThemedText style={styles.tableCell}>{b.overs}</ThemedText>
          <ThemedText style={styles.tableCell}>{b.maidens ?? 0}</ThemedText>
          <ThemedText style={styles.tableCell}>{b.runs}</ThemedText>
          <ThemedText style={styles.tableCell}>{b.wickets}</ThemedText>
          <ThemedText style={styles.tableCell}>{b.econ}</ThemedText>
        </View>
      ))}
    </View>
  );
}

function AggressionSlider({
  label,
  value,
  onChange,
  accent,
  disabled,
  lowLabel = 'defend',
  highLabel = 'attack',
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  accent?: string;
  disabled?: boolean;
  min?: number;
  max?: number;
  lowLabel?: string;
  highLabel?: string;
}) {
  const theme = useTheme();
  return (
    <View style={[styles.aggWrap, disabled && styles.choiceDisabled]}>
      <ThemedText themeColor="textDim" style={styles.fieldLabel}>
        {label}
      </ThemedText>
      <View style={styles.aggRow}>
        {[1, 2, 3, 4, 5].map((n) => (
          <Pressable
            key={n}
            disabled={disabled}
            onPress={() => onChange(n)}
            style={[
              styles.aggDot,
              { borderColor: theme.border },
              n === value && { backgroundColor: accent ?? theme.green, borderColor: accent ?? theme.green },
            ]}>
            <ThemedText style={[styles.aggDotText, n === value && { color: '#1a1404' }]}>{n}</ThemedText>
          </Pressable>
        ))}
      </View>
      <View style={styles.rowBetween}>
        <ThemedText themeColor="textFaint" style={styles.aggHint}>
          1 {lowLabel}
        </ThemedText>
        <ThemedText themeColor="textFaint" style={styles.aggHint}>
          5 {highLabel}
        </ThemedText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: Spacing.three,
  },
  stage: {
    gap: Spacing.three,
  },
  busyOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  errorText: {
    fontSize: 12.5,
  },
  noticeBanner: {
    borderWidth: 2,
    borderRadius: Radius.md,
    padding: Spacing.two,
    marginBottom: Spacing.two,
  },
  scoreboard: {
    borderRadius: Radius.md,
    padding: Spacing.three,
    paddingTop: Spacing.three + 2,
    gap: 6,
  },
  scoreboardSmall: {
    fontSize: 12,
    lineHeight: 17,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.85)',
  },
  scoreboardSmallStrong: {
    fontWeight: '800',
    color: '#fff',
  },
  scoreboardTeam: {
    fontSize: 13,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.9)',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  scoreboardLine: {
    fontSize: 34,
    lineHeight: 42,
    fontWeight: '900',
    color: '#fff',
  },
  scoreboardOvers: {
    fontSize: 15,
    lineHeight: 42,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.85)',
  },
  scoreboardMessage: {
    fontSize: 13,
    lineHeight: 19,
    color: '#fff',
  },
  scoreboardScoreRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: Spacing.two,
    marginTop: 2,
  },
  batterLine: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  strikeMark: {
    width: 12,
    fontSize: 13,
    fontWeight: '800',
    color: '#fff',
  },
  batterName: {
    flex: 1,
    fontSize: 13,
    fontWeight: '700',
    color: '#fff',
  },
  batterFigs: {
    fontSize: 13,
    fontWeight: '800',
    color: '#fff',
  },
  scoreboardDivider: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: Spacing.two,
    paddingTop: 4,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255,255,255,0.25)',
  },
  // Current-over strip: bowler line stacked above the ball chips so a long
  // bowler name never squeezes the chips off-screen — they wrap full-width.
  currentOverBlock: {
    gap: 4,
    paddingTop: 4,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255,255,255,0.25)',
  },
  panelTitle: {
    fontSize: 15,
    fontWeight: '800',
    marginBottom: 4,
  },
  helpText: {
    fontSize: 12,
    lineHeight: 18,
    marginBottom: Spacing.two,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: Spacing.two,
    marginTop: Spacing.two,
  },
  rowBetween: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
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
  fieldLabel: {
    fontSize: 11.5,
    fontWeight: '600',
    marginBottom: 4,
  },
  choiceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.two,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  choiceDisabled: {
    opacity: 0.4,
  },
  flex1: {
    flex: 1,
    minWidth: 0,
  },
  choiceName: {
    fontSize: 13.5,
    fontWeight: '700',
  },
  choiceSub: {
    fontSize: 11,
    marginTop: 2,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxMark: {
    color: '#1a1404',
    fontWeight: '800',
    fontSize: 13,
  },
  radio: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  overLogRow: {
    marginBottom: Spacing.two,
  },
  overLogTitle: {
    fontSize: 12.5,
    fontWeight: '700',
    marginBottom: 4,
  },
  overLogBalls: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  ballChip: {
    minWidth: 26,
    height: 26,
    borderRadius: Radius.sm,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
  },
  ballChipText: {
    fontSize: 11,
    fontWeight: '800',
  },
  wicketNote: {
    fontSize: 11,
    marginTop: 2,
  },
  miniGrid: {
    flexDirection: 'row',
    gap: Spacing.three,
  },
  miniRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  miniName: {
    fontSize: 12,
    flexShrink: 1,
    marginRight: 6,
  },
  miniValue: {
    fontSize: 12,
    fontWeight: '700',
  },
  tableHeaderRow: {
    flexDirection: 'row',
    paddingBottom: 6,
  },
  tableHeaderCell: {
    flex: 1,
    fontSize: 10,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    textAlign: 'right',
  },
  tableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  tableNameCol: {
    flex: 2.4,
    textAlign: 'left',
  },
  tableName: {
    fontSize: 12.5,
    fontWeight: '700',
  },
  tableDismissal: {
    fontSize: 10,
    marginTop: 1,
  },
  tableCell: {
    flex: 1,
    fontSize: 12.5,
    textAlign: 'right',
  },
  aggWrap: {
    marginBottom: Spacing.two,
  },
  aggRow: {
    flexDirection: 'row',
    gap: 6,
    marginBottom: 2,
  },
  aggDot: {
    flex: 1,
    height: 32,
    borderRadius: Radius.sm,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  aggDotText: {
    fontSize: 13,
    fontWeight: '700',
  },
  aggHint: {
    fontSize: 10,
  },
});
