/**
 * Design tokens translated from docs/mockups/phase1-mockups.html.
 * Mirrors the CSS custom properties defined there for dark (default) and light themes.
 */

import '@/global.css';

import { Platform } from 'react-native';

export const Colors = {
  light: {
    text: '#1a2233',
    textDim: '#6b7589',
    textFaint: '#a4abbb',
    background: '#f4f5f8',
    backgroundElement: '#ffffff',
    backgroundSelected: '#e3e6ed',
    textSecondary: '#6b7589',
    // mockup tokens
    bg: '#f4f5f8',
    bgElevated: '#ffffff',
    bgCard: '#ffffff',
    border: '#e3e6ed',
    green: '#1f9d55',
    red: '#e0483e',
    badgeBg: 'rgba(20,30,60,0.06)',
    badgeBgStrong: 'rgba(20,30,60,0.1)',
    bottomNavBg: 'rgba(255,255,255,0.92)',
  },
  dark: {
    text: '#eef1f6',
    textDim: '#8e9bb3',
    textFaint: '#5d6b85',
    background: '#0b0f17',
    backgroundElement: '#1a2233',
    backgroundSelected: '#2a3346',
    textSecondary: '#8e9bb3',
    // mockup tokens
    bg: '#0b0f17',
    bgElevated: '#141a26',
    bgCard: '#1a2233',
    border: '#2a3346',
    green: '#3ddc84',
    red: '#ff5d5d',
    badgeBg: 'rgba(255,255,255,0.08)',
    badgeBgStrong: 'rgba(255,255,255,0.14)',
    bottomNavBg: 'rgba(11,15,23,0.94)',
  },
} as const;

export type ThemeColor = keyof typeof Colors.light & keyof typeof Colors.dark;

export const Fonts = Platform.select({
  ios: {
    /** iOS `UIFontDescriptorSystemDesignDefault` */
    sans: 'system-ui',
    /** iOS `UIFontDescriptorSystemDesignSerif` */
    serif: 'ui-serif',
    /** iOS `UIFontDescriptorSystemDesignRounded` */
    rounded: 'ui-rounded',
    /** iOS `UIFontDescriptorSystemDesignMonospaced` */
    mono: 'ui-monospace',
  },
  default: {
    sans: 'normal',
    serif: 'serif',
    rounded: 'normal',
    mono: 'monospace',
  },
  web: {
    sans: 'var(--font-display)',
    serif: 'var(--font-serif)',
    rounded: 'var(--font-rounded)',
    mono: 'var(--font-mono)',
  },
});

export const Spacing = {
  half: 2,
  one: 4,
  two: 8,
  three: 16,
  four: 24,
  five: 32,
  six: 64,
} as const;

/** Corner radius used for cards, buttons, and badges (--radius in mockups). */
export const Radius = {
  sm: 8,
  md: 14,
  lg: 20,
  pill: 999,
} as const;

/**
 * Approximate height of the native bottom tab bar, including the device's
 * home-indicator safe area (e.g. ~83pt on Face ID iPhones, ~50pt base + ~33pt
 * inset). `expo-router`'s `NativeTabs` does not automatically inset our
 * `ScrollView`s, so screens add this to their bottom content padding.
 */
export const BottomTabInset = Platform.select({ ios: 50, android: 80 }) ?? 0;
export const MaxContentWidth = 800;

/**
 * Reserved space at the bottom of scrollable screen content so it never sits
 * underneath the bottom tab bar — the floating pill bar on web (see
 * app-tabs.web.tsx), or the native tab bar (plus home-indicator inset) on iOS
 * and Android.
 */
export const WebTabBarHeight = 92;
export const ContentBottomInset = (
  Platform.OS === 'web'
    ? (`calc(${WebTabBarHeight}px + env(safe-area-inset-bottom, 0px))` as unknown as number)
    : BottomTabInset + Spacing.five
);

/**
 * Per-team primary/accent colors, matching TEAM_META in
 * packages/sim_engine/src/cricket_sim_engine/sim/constants.py.
 * `accentText` is a legible variant of `accent` for foreground text/icons
 * (vivid in dark mode, darkened toward body text in light mode).
 */
export const TeamColors: Record<string, { abbr: string; primary: string; accent: string }> = {
  'Chennai Cholas': { abbr: 'CHE', primary: '#e8a013', accent: '#0f2a5c' },
  'Mumbai Mavericks': { abbr: 'MUM', primary: '#1f6feb', accent: '#f0c419' },
  'Bengaluru Bulls': { abbr: 'BLR', primary: '#9b1d3a', accent: '#1c1c24' },
  'Kolkata Knights': { abbr: 'KOL', primary: '#6b3fa0', accent: '#e0b94a' },
  'Hyderabad Hawks': { abbr: 'HYD', primary: '#e8602c', accent: '#143d59' },
  'Rajasthan Raptors': { abbr: 'RAJ', primary: '#c2185b', accent: '#0e9aa7' },
  'Delhi Dynamos': { abbr: 'DEL', primary: '#0b6e6e', accent: '#f24236' },
  'Gujarat Gladiators': { abbr: 'GUJ', primary: '#1a2238', accent: '#d4943a' },
  'Lucknow Lions': { abbr: 'LKO', primary: '#0f8a8a', accent: '#f2a541' },
  'Punjab Panthers': { abbr: 'PUN', primary: '#5a3e8e', accent: '#e8505b' },
};

export const TEAM_NAMES = Object.keys(TeamColors);

/**
 * Minimal team branding shape needed by the color helpers below. Pass the
 * actual `TeamDict` from the API payload (or any subset of these fields)
 * rather than a team name — names can be changed via the rename flow, so a
 * static name -> color lookup silently falls back to a neutral default the
 * moment a team's display name no longer matches a TeamColors key. The
 * backend already resolves these fields in a rename-safe way (via
 * `meta_name`) and ships them on every team object.
 */
export interface TeamMeta {
  abbr?: string;
  primary: string;
  accent: string;
}

/**
 * Resolves a `TeamMeta` for a team name via the static `TeamColors` table.
 * Only use this where no team/payload object is available (e.g. the
 * new-career franchise picker, before any team has been created) — anywhere
 * a `TeamDict` is already in scope, pass it directly to the helpers below
 * instead so a renamed team keeps its color.
 */
export function teamMetaByName(teamName: string): TeamMeta {
  return TeamColors[teamName] ?? { abbr: '', primary: '#3a3f4b', accent: '#9aa0a6' };
}

/**
 * Hand-tuned, theme-aware team swatch colors used by filter dropdowns and
 * chips. Each entry has a `dark` and `light` color used as the *foreground*
 * (accent text / dot); the surrounding bubble is a low-alpha tint of it.
 *
 * `light` is the team's primary (nudged darker where it'd be unreadable on
 * white); `dark` is a brightened version so it reads as a light accent on a
 * dark bubble. Teams whose primary is near-black/navy (Bengaluru, Gujarat)
 * use their vivid accent instead so all ten stay distinct.
 */
export const TeamSwatches: Record<string, { dark: string; light: string }> = {
  'Chennai Cholas': { dark: '#f4bc3a', light: '#c8870f' },
  'Mumbai Mavericks': { dark: '#5a9cf5', light: '#1f6feb' },
  'Bengaluru Bulls': { dark: '#e8466a', light: '#9b1d3a' },
  'Kolkata Knights': { dark: '#a37fd6', light: '#5a2d91' },
  'Hyderabad Hawks': { dark: '#f5894f', light: '#d4521f' },
  'Rajasthan Raptors': { dark: '#f0508f', light: '#c2185b' },
  'Delhi Dynamos': { dark: '#2bb3b3', light: '#0b6e6e' },
  'Gujarat Gladiators': { dark: '#e0b665', light: '#a8801f' },
  'Lucknow Lions': { dark: '#2bc0c0', light: '#0f8a8a' },
  'Punjab Panthers': { dark: '#9a78d8', light: '#5a3e8e' },
};

/**
 * The accent color to use for a team in the given scheme — a light, legible
 * tone in dark mode and the (near-)official color in light mode. Used as the
 * foreground for swatch dots and selected-filter text. Falls back to the
 * existing primary/accent derivation if a team has no tuned swatch.
 */
export function getTeamSwatch(team: TeamMeta, teamName: string, scheme: 'light' | 'dark'): string {
  const tuned = TeamSwatches[teamName];
  if (tuned) return tuned[scheme];
  return getTeamPlayerAccent(team, scheme);
}

/** Champagne/trophy gold accent used to highlight playoff and Final UI. */
export const GOLD = '#f0b429';

/**
 * Short team code (e.g. "Chennai Cholas" -> "CHE") for compact labels.
 * Prefer the `abbr` already shipped on a `TeamDict`/`MatchCard`-adjacent
 * object — it's rename-safe. Falls back to the static table (keyed by
 * canonical franchise name) or a 3-letter slice of the raw name as a last
 * resort, for places that only ever have a bare team-name string.
 */
export function teamAbbr(teamName: string, abbr?: string): string {
  return abbr || TeamColors[teamName]?.abbr || teamName;
}

/** Mixes a hex color toward another hex color by `amount` (0-1). */
function mixHex(hex: string, towardHex: string, amount: number): string {
  const a = hex.replace('#', '');
  const b = towardHex.replace('#', '');
  const ar = parseInt(a.slice(0, 2), 16);
  const ag = parseInt(a.slice(2, 4), 16);
  const ab = parseInt(a.slice(4, 6), 16);
  const br = parseInt(b.slice(0, 2), 16);
  const bg = parseInt(b.slice(2, 4), 16);
  const bb = parseInt(b.slice(4, 6), 16);
  const r = Math.round(ar + (br - ar) * amount);
  const g = Math.round(ag + (bg - ag) * amount);
  const bch = Math.round(ab + (bb - ab) * amount);
  return `#${[r, g, bch].map((v) => v.toString(16).padStart(2, '0')).join('')}`;
}

/**
 * Returns a legible "accent text" color for a team in the given scheme,
 * matching --team-accent-text in the mockups (vivid in dark mode,
 * blended 65/35 toward body text in light mode).
 */
export function getTeamAccentText(team: TeamMeta, scheme: 'light' | 'dark'): string {
  const vivid = vividTeamColor(team);
  if (scheme === 'dark') return vivid;
  return mixHex(vivid, Colors.light.text, 0.35);
}

/**
 * Whether a hex color is effectively black, white, or gray — i.e. its red,
 * green, and blue channels are all close together. Used to steer "accent"
 * colors (position badges, OVR figures, crest text) away from a team's
 * grayscale color (e.g. RCB's near-black accent, GT's near-black primary,
 * PBKS's silver accent) toward its more vivid color (RCB red, GT gold).
 */
function isGrayscale(hex: string): boolean {
  const h = hex.replace('#', '');
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return Math.max(r, g, b) - Math.min(r, g, b) < 24;
}

/**
 * Picks whichever of a team's two colors (`primary`/`accent`) is more vivid
 * (not grayscale), for use as a small "accent" highlight — position badges,
 * OVR figures, crest text. Falls back to `accent` if both or neither color
 * is grayscale.
 */
function vividTeamColor(meta: { primary: string; accent: string }): string {
  const accentGray = isGrayscale(meta.accent);
  const primaryGray = isGrayscale(meta.primary);
  if (accentGray && !primaryGray) return meta.primary;
  return meta.accent;
}

/** Relative luminance of a hex color, in the range 0 (black) to 1 (white). */
function relativeLuminance(hex: string): number {
  const h = hex.replace('#', '');
  const r = parseInt(h.slice(0, 2), 16) / 255;
  const g = parseInt(h.slice(2, 4), 16) / 255;
  const b = parseInt(h.slice(4, 6), 16) / 255;
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * Picks a legible foreground color (near-black or near-white) for text/icons
 * drawn on top of `backgroundHex`, based on relative luminance. Used for
 * buttons, segmented controls, and chips that take an arbitrary team color
 * as their background — some team colors are very dark (e.g. RCB, GT) and
 * others very light (e.g. PBKS, CSK), so a single hardcoded text color
 * doesn't stay readable across all of them.
 */
export function getContrastText(backgroundHex: string): string {
  return relativeLuminance(backgroundHex) > 0.55 ? '#1a1404' : '#ffffff';
}

/** Saturation of a hex color (HSL S), 0 (gray) to 1 (fully saturated). */
function saturation(hex: string): number {
  const h = hex.replace('#', '');
  const r = parseInt(h.slice(0, 2), 16) / 255;
  const g = parseInt(h.slice(2, 4), 16) / 255;
  const b = parseInt(h.slice(4, 6), 16) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  if (max === min) return 0;
  const l = (max + min) / 2;
  return l > 0.5 ? (max - min) / (2 - max - min) : (max - min) / (max + min);
}

/**
 * A solid, saturated team color for use as a FILLED background (scoreboard,
 * primary match buttons) with white text on top. Picks whichever of the
 * team's two colors is the most vivid (avoiding near-black/near-white/gray
 * identity colors like SRH's black or PBKS's silver), then darkens very light
 * picks (CSK gold) so white text stays legible. Always returns a color dark
 * enough for `#fff` foreground.
 */
export function getTeamBackground(team: TeamMeta, teamName?: string): string {
  // Prefer the more saturated of the two team colors; that skips grayscale.
  const candidate = saturation(team.primary) >= saturation(team.accent) ? team.primary : team.accent;
  // If even the better candidate is washed-out gray, fall back to the swatch.
  const base = saturation(candidate) < 0.15 ? (teamName && TeamSwatches[teamName]?.light) || candidate : candidate;
  // Ensure it's dark enough for white text; darken toward near-black if needed.
  return relativeLuminance(base) > 0.5 ? mixHex(base, '#111111', 0.45) : base;
}

/**
 * Given a team's two colors, returns the lighter one as a pill background
 * and the darker one as its text color — a two-tone team look without a
 * separate stripe/dot. Falls back to black/white text if the darker color
 * doesn't read well enough on the lighter one.
 */
export function pickPillColors(colorA: string, colorB: string): { background: string; text: string } {
  const [light, dark] =
    relativeLuminance(colorA) >= relativeLuminance(colorB) ? [colorA, colorB] : [colorB, colorA];
  const contrast = Math.abs(relativeLuminance(light) - relativeLuminance(dark));
  return { background: light, text: contrast > 0.25 ? dark : getContrastText(light) };
}

/**
 * Returns a version of `accentHex` that stays legible as text on a tinted
 * version of itself (as used by Pill's accent style). Very light colors
 * (e.g. Punjab Panthers' silver `#b7b7b7`) are blended toward the theme's body
 * text color so they don't wash out against light/dark card backgrounds.
 */
export function getReadableAccentText(accentHex: string, scheme: 'light' | 'dark'): string {
  const luminance = relativeLuminance(accentHex);
  if (scheme === 'light' && luminance > 0.6) {
    return mixHex(accentHex, Colors.light.text, 0.5);
  }
  if (scheme === 'dark' && luminance < 0.18) {
    return mixHex(accentHex, Colors.dark.text, 0.5);
  }
  return accentHex;
}

/**
 * A strongly legible version of `accentHex` for use as PROMINENT value text on
 * a card background (e.g. leaderboard stat figures). Unlike
 * `getReadableAccentText` (a subtle 50% nudge for chips), this pushes a too-dark
 * (dark mode) or too-light (light mode) accent most of the way to the theme's
 * body text color so the number reads clearly; mid-tone accents pass through.
 */
export function getLegibleAccentValue(accentHex: string, scheme: 'light' | 'dark'): string {
  const luminance = relativeLuminance(accentHex);
  if (scheme === 'dark' && luminance < 0.4) {
    return mixHex(accentHex, Colors.dark.text, 0.8);
  }
  if (scheme === 'light' && luminance > 0.7) {
    return mixHex(accentHex, Colors.light.text, 0.8);
  }
  return accentHex;
}

/**
 * Picks whichever of a team's two colors (`primary`/`accent`) reads best as
 * small text/numbers on a card background in the given scheme, e.g. for
 * Squad's OVR figures and role badges. CSK's accent (navy `#22409a`) is
 * nearly invisible on dark cards, so dark mode falls back to its bright
 * primary (`#f7c948`); a team whose primary is itself too light for light
 * mode falls back the other way. If neither color is a good fit, blends
 * the accent toward the theme's body text color.
 */
export function getTeamPlayerAccent(team: TeamMeta, scheme: 'light' | 'dark'): string {
  const vivid = vividTeamColor(team);
  const candidates = [vivid, team.accent, team.primary];
  const fits = (hex: string) => {
    const luminance = relativeLuminance(hex);
    return scheme === 'dark' ? luminance > 0.35 : luminance < 0.7;
  };

  const best = candidates.find(fits);
  if (best) return best;

  return getReadableAccentText(vivid, scheme);
}
