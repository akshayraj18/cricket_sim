/**
 * Contrast guarantees for team-coloured surfaces.
 *
 * Team colours are data, not design decisions — a new franchise can be added
 * with any hex — so legibility has to be a property of the helpers rather than
 * something checked by eye per team. These are the cases that actually broke:
 * a captain badge rendering near-black on a dark fill, and filled buttons
 * showing white text at 1.9:1.
 */
import {
  darkenForWhiteText,
  getContrastText,
  getTeamBackground,
  getTeamPlayerAccent,
  InternationalTeamColors,
  TeamColors,
  WorldTeamColors,
} from '../theme';

/** WCAG relative luminance. */
function luminance(hex: string): number {
  const h = hex.replace('#', '');
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string): number {
  const [l1, l2] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (l1 + 0.05) / (l2 + 0.05);
}

const ALL_TEAMS = Object.entries({
  ...TeamColors,
  ...InternationalTeamColors,
  ...WorldTeamColors,
});

// WCAG AA for normal text. Badges are small and bold, so 4.5 is the honest bar.
const AA = 4.5;

describe('getTeamBackground — filled surfaces under white text', () => {
  it.each(ALL_TEAMS)('%s fill clears AA with white text', (name, team) => {
    const fill = getTeamBackground(team, name);
    expect(contrast(fill, '#ffffff')).toBeGreaterThanOrEqual(AA);
  });

  it.each(ALL_TEAMS)('%s fill still resolves to white text, not dark', (name, team) => {
    // The design language is white-on-team-colour. Deepening the fill (rather
    // than flipping the text) is what keeps that intact, and it should land
    // below getContrastText's black/white crossover so the helper agrees.
    const fill = getTeamBackground(team, name);
    expect(getContrastText(fill)).toBe('#ffffff');
  });
});

describe('getContrastText — picks the more legible candidate', () => {
  it('prefers dark text on a mid-tone where white would be worse', () => {
    // Rajasthan's teal: white measured 1.9:1, near-black 4.2:1. A fixed
    // luminance cutoff of 0.55 chose white here.
    const midTone = '#0e9aa7';
    const chosen = getContrastText(midTone);
    expect(contrast(midTone, chosen)).toBeGreaterThan(contrast(midTone, '#ffffff'));
  });

  it.each(ALL_TEAMS)('%s captain badge is legible in both themes', (name, team) => {
    // Mirrors what PlayerRow renders: the accent is deepened until white works.
    // Picking a text colour alone is not enough — Kolkata's purple manages only
    // 2.9:1 with white and 2.8:1 with black, so no choice of text saves it.
    for (const scheme of ['light', 'dark'] as const) {
      const badgeFill = darkenForWhiteText(getTeamPlayerAccent(team, scheme));
      expect(contrast(badgeFill, '#ffffff')).toBeGreaterThanOrEqual(AA);
    }
  });

  it('never returns a colour worse than the alternative', () => {
    for (const [, team] of ALL_TEAMS) {
      for (const hex of [team.primary, team.accent]) {
        const chosen = getContrastText(hex);
        const other = chosen === '#ffffff' ? '#1a1404' : '#ffffff';
        expect(contrast(hex, chosen)).toBeGreaterThanOrEqual(contrast(hex, other));
      }
    }
  });
});
