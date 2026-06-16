/**
 * Steps for the guided tour. The tour is fully automated and read-only: it
 * creates a throwaway demo career up front (mega draft, autodrafted to a full
 * season) and then drives the REAL app screen by screen, freezing the app and
 * spotlighting the relevant region for each step. The user only taps
 * Back/Next/Skip; the demo career is deleted when the tour ends.
 *
 * Each step selects a `tab` and a `spotlight` region. `squadTab` opens a Squad
 * sub-tab (read by the Squad screen via TourContext) so the right sub-screen is
 * shown — e.g. 'batting' = Starting XI.
 */
export interface TutorialStep {
  key: string;
  emoji: string;
  title: string;
  body: string;
  /** Native tab to select (one of: index, squad, season, stats, history). */
  tab?: 'index' | 'squad' | 'season' | 'stats' | 'history';
  /**
   * Which region of the screen to spotlight (left bright; the rest is dimmed
   * and tap-blocked). The instruction card is placed away from the spotlight:
   * - 'tabbar'  — the bottom tab bar
   * - 'header'  — the top title / sub-tab area
   * - 'content' — the full working area, from the title down to the tab bar
   * - 'screen'  — the whole screen (intro/outro, no cut-out)
   */
  spotlight?: 'tabbar' | 'header' | 'content' | 'screen';
  /**
   * For squad-screen steps, which sub-tab to open while the step is showing
   * (the Squad screen reads this from TourContext). 'batting' = Starting XI.
   */
  squadTab?: 'roster' | 'batting' | 'bowling' | 'leadership';
  /**
   * If set, advancing INTO this step autodrafts the demo career to completion,
   * so this and following screens have a full 25-man roster and an open season.
   * Set on the first post-draft step so the draft board stays live until then.
   */
  fillSquad?: boolean;
}

export const TUTORIAL_STEPS: TutorialStep[] = [
  {
    key: 'welcome',
    emoji: '🏏',
    title: 'Welcome, Manager',
    body: "Sit back — this tour drives the app for you. We’ve started a demo career so you can see every screen with real data. Just tap Next to move along; the highlighted area shows what each step is about.",
    spotlight: 'screen',
  },
  {
    key: 'home',
    emoji: '🏠',
    title: 'Home & New Career',
    body: 'The Home tab is your dashboard — your current career at a glance, and the “New Career” button to start one. You pick a franchise, a difficulty, and how to build your squad: the real 2026 rosters, or a mega draft (what we chose for this demo).',
    tab: 'index',
    spotlight: 'content',
  },
  {
    key: 'tabbar',
    emoji: '🧭',
    title: 'Getting Around',
    body: 'These tabs along the bottom are how you move around: Home, Squad, Season, Stats, and History. We’ll visit each one now.',
    tab: 'index',
    spotlight: 'tabbar',
  },
  {
    key: 'draft',
    emoji: '📋',
    title: 'The Mega Draft',
    body: 'A mega draft builds your 25-player squad pick by pick — snake order, every franchise competing, max 9 overseas. You can draft manually, autodraft a pick, or let the CPU finish. We autodrafted this demo squad so the rest of the app has players to show.',
    tab: 'season',
    spotlight: 'content',
  },
  {
    key: 'squad',
    emoji: '🧢',
    title: 'Squad: Starting XI',
    body: 'This is the Squad tab’s Starting XI screen. Here you tap a slot to swap a player, set your Impact Sub, and arrange the batting order — or tap “Autofill” for smart defaults. The sub-tabs above cover your full roster, the bowling plan, and leadership.',
    tab: 'squad',
    spotlight: 'content',
    squadTab: 'batting',
    fillSquad: true,
  },
  {
    key: 'season',
    emoji: '🎮',
    title: 'Play the Season',
    body: 'The Season tab runs your fixtures. Quick-sim a match day for instant results, or enter the Match Centre to play it live, ball by ball. The points table climbs toward the playoffs as results come in.',
    tab: 'season',
    spotlight: 'content',
  },
  {
    key: 'stats',
    emoji: '📊',
    title: 'Track Everything',
    body: 'The Stats tab has the full points table, the Orange and Purple Cap races, and the MVP leaderboard. Tap any player to see their season card.',
    tab: 'stats',
    spotlight: 'content',
  },
  {
    key: 'history',
    emoji: '🏆',
    title: 'Build a Legacy',
    body: 'The History tab archives every season you finish — champions, runners-up, season MVPs, and your all-time leaders across careers. This is your dynasty’s record book.',
    tab: 'history',
    spotlight: 'content',
  },
  {
    key: 'done',
    emoji: '🚀',
    title: "You're Ready",
    body: 'That’s the whole loop: draft, manage, play, repeat. We’ll clear this demo career and drop you back Home so you can start one for real. You can replay this tour any time from the account menu.',
    tab: 'index',
    spotlight: 'screen',
  },
];

/** Legacy alias so older imports of TUTORIAL_SLIDES keep working. */
export type TutorialSlide = TutorialStep;
export const TUTORIAL_SLIDES = TUTORIAL_STEPS;
