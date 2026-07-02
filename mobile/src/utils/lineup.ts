import { PlayerDict, TeamDict } from '@/api/types';

/** Batting order slot groupings used across all formats. */
export const ORDER_ZONES = [
  { key: 'top', label: 'Openers', range: [1, 2] as const },
  { key: 'middle', label: 'Middle Order', range: [3, 5] as const },
  { key: 'lower', label: 'Lower Order', range: [6, 7] as const },
  { key: 'tail', label: 'Tail', range: [8, 11] as const },
];

/** T20 bowling phase groupings for the bowling plan. */
export const OVER_PHASE_ZONES = [
  { key: 'powerplay', label: 'Powerplay', range: [1, 6] as const },
  { key: 'middle', label: 'Middle Overs', range: [7, 15] as const },
  { key: 'death', label: 'Death Overs', range: [16, 20] as const },
];

export function zoneForSlot(slotNumber: number, zones = ORDER_ZONES) {
  return zones.find((z) => slotNumber >= z.range[0] && slotNumber <= z.range[1]) ?? zones[Math.floor(zones.length / 2)];
}

export function slotZoneLabel(slotNumber: number | undefined): string {
  return zoneForSlot(slotNumber ?? 6).label;
}

/** Returns up to 11 unique names: preferred order first (filtered to roster), then fills with remaining roster names. Mirrors uniqueXi(). */
export function uniqueXi(names: string[], roster: PlayerDict[]): string[] {
  const rosterNames = roster.map((p) => p.name);
  const picked: string[] = [];
  for (const name of names || []) {
    if (rosterNames.includes(name) && !picked.includes(name) && picked.length < 11) picked.push(name);
  }
  for (const name of rosterNames) {
    if (!picked.includes(name) && picked.length < 11) picked.push(name);
  }
  return picked;
}

export function benchNames(roster: PlayerDict[], xi: string[]): string[] {
  return roster.map((p) => p.name).filter((name) => !xi.includes(name));
}

/** Players from `names` who are eligible to bowl (Bowler or All-Rounder). Mirrors bowlingOptions(). */
export function bowlingOptions(names: string[], roster: PlayerDict[]): string[] {
  const byName = new Map(roster.map((p) => [p.name, p]));
  return names
    .map((n) => byName.get(n))
    .filter((p): p is PlayerDict => !!p && (p.role.includes('Bowler') || p.role === 'All-Rounder'))
    .map((p) => p.name);
}

/** Mirrors xiValidationError(). Returns an error message, or "" if valid. */
export function xiValidationError(names: string[], label: string, roster: PlayerDict[]): string {
  const clean = names.filter(Boolean);
  const duplicates = [...new Set(clean.filter((name, i) => clean.indexOf(name) !== i))];
  if (clean.length !== 11) return `${label} must contain 11 players.`;
  if (new Set(clean).size !== 11) return `${label} has duplicate players: ${duplicates.join(', ')}.`;
  const byName = new Map(roster.map((p) => [p.name, p]));
  const players = clean.map((n) => byName.get(n)).filter((p): p is PlayerDict => !!p);
  if (players.filter((p) => ['Batsman', 'Wicketkeeper', 'All-Rounder'].includes(p.role)).length < 6) {
    return `${label} needs at least 6 batting options.`;
  }
  if (players.filter((p) => p.overseas).length > 4) return `${label} cannot include more than 4 overseas players.`;
  return '';
}

/** Returns an error message if `impactSubName` isn't a valid Impact Sub choice, or "" if valid. */
export function impactSubError(impactSubName: string, startingXi: string[], roster: PlayerDict[]): string {
  if (!impactSubName || !roster.some((p) => p.name === impactSubName)) {
    return 'Choose an Impact Sub from your squad.';
  }
  if (startingXi.includes(impactSubName)) return 'Impact Sub must not already be in the Starting XI.';
  return '';
}

/** Mirrors bowlingPlanError(). names.length must be 0 (blank/auto) or 20. */
export function bowlingPlanError(names: string[], label = 'Bowling plan'): string {
  if (!names.length) return '';
  if (names.length !== 20) return `${label} must contain all 20 overs, or be left completely blank.`;
  const overbowled = [...new Set(names)].filter((name) => names.filter((x) => x === name).length > 4);
  if (overbowled.length) return `${label} has a bowler above the 4-over limit: ${overbowled.join(', ')}.`;
  const repeatAt = names.find((name, i) => i > 0 && name === names[i - 1]);
  return repeatAt ? `${label} cannot use ${repeatAt} in consecutive overs.` : '';
}

export function teamAccent(team: TeamDict | undefined): string {
  return team?.accent ?? '#3ddc84';
}

/** Score a bowler's fit for a given over phase. */
function bowlingPlanScore(p: PlayerDict, phase: string): number {
  let score = Number(p.bowl) || 0;
  const bowlType = `${p.bowling_type || ''} ${p.bowling_phase || ''}`;
  if (p.bowling_phase === phase) score += 10;
  if (phase === 'Powerplay' && /Swing|Fast|Medium|Seam|New-ball/i.test(bowlType)) score += 5;
  if (phase === 'Middle Overs' && /Spin|Orthodox|Leg|Off|Mystery/i.test(bowlType)) score += 7;
  if (phase === 'Death Overs' && /Death|Fast|Variations|Yorker/i.test(bowlType)) score += 7;
  return score;
}

/**
 * Builds a 20-over bowling plan from the eligible bowlers in `bowlFirst`,
 * picking the best-fit bowler for each over's phase (Powerplay/Middle/Death)
 * while respecting the 4-over cap and no-consecutive-overs rule.
 */
export function autofillBowlingPlan(bowlFirst: string[], roster: PlayerDict[]): string[] {
  const eligibleNames = bowlingOptions(bowlFirst, roster);
  const byName = new Map(roster.map((p) => [p.name, p]));
  const eligible = eligibleNames.map((n) => byName.get(n)).filter((p): p is PlayerDict => !!p);

  const used: Record<string, number> = {};
  const plan: string[] = [];
  for (let over = 0; over < 20; over += 1) {
    const phase = over < 6 ? 'Powerplay' : over < 15 ? 'Middle Overs' : 'Death Overs';
    const last = plan.at(-1);
    const candidates = eligible.filter((p) => (used[p.name] ?? 0) < 4 && p.name !== last);
    const pool = candidates.length ? candidates : eligible.filter((p) => (used[p.name] ?? 0) < 4);
    if (!pool.length) break;
    const chosen = [...pool].sort((a, b) => bowlingPlanScore(b, phase) - bowlingPlanScore(a, phase))[0];
    plan.push(chosen.name);
    used[chosen.name] = (used[chosen.name] ?? 0) + 1;
  }
  return plan;
}
