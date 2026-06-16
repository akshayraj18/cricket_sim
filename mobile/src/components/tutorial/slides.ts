/**
 * Steps for the guided tour. Unlike a standalone carousel, each step points at
 * a REAL screen in the app: the tour navigates there, dims it, and floats a
 * tooltip card explaining what you do on that screen. Kept as plain data so the
 * tour component stays presentation-only and the copy is easy to tweak.
 *
 * `route` is the expo-router path the tour navigates to before showing the step
 * (omit for an intro/outro step shown over whatever is on screen). `tab` is the
 * native-tab trigger name to select, when the step lives under the tab bar.
 * `placement` positions the tooltip card so it doesn't cover the area the step
 * is talking about.
 */
export interface TutorialStep {
  key: string;
  emoji: string;
  title: string;
  body: string;
  /** Route to navigate to before showing this step. */
  route?: string;
  /** Native tab to select (one of: index, squad, season, stats, history). */
  tab?: 'index' | 'squad' | 'season' | 'stats' | 'history';
  /**
   * Which region of the screen to spotlight (cut out of the dim so the real UI
   * shows through brightly there). The instruction card is placed away from the
   * spotlight automatically:
   * - 'tabbar'  — the bottom tab bar
   * - 'header'  — the top app-bar / screen title area
   * - 'content' — the main panel area (centre band)
   * - 'screen'  — the whole screen (intro/outro steps, no cut-out)
   */
  spotlight?: 'tabbar' | 'header' | 'content' | 'screen';
  /**
   * If set, advancing INTO this step ensures a career exists and its draft is
   * open: the tour creates a mega-draft career (if the user has none) and starts
   * the draft, so the draft board shows real franchises + the player pool.
   */
  ensureCareer?: boolean;
  /**
   * If set, advancing INTO this step finishes the draft (autodraft all) so the
   * squad/Starting-XI/season screens that follow have a full 25-man roster and
   * an open season. No-op once the season is already underway.
   */
  fillSquad?: boolean;
  /**
   * For squad-screen steps, which sub-tab to open while the step is showing
   * (the Squad screen reads this from TourContext). 'batting' = Starting XI.
   */
  squadTab?: 'roster' | 'batting' | 'bowling' | 'leadership';
}

export const TUTORIAL_STEPS: TutorialStep[] = [
  {
    key: 'welcome',
    emoji: '🏏',
    title: 'Welcome, Manager',
    body: "This quick tour moves around the real app, highlighting each part as we go. The screen behind stays live — watch the spotlighted area for what each step describes. Tap Next to begin.",
    spotlight: 'screen',
  },
  {
    key: 'home',
    emoji: '🏠',
    title: 'The Tab Bar',
    body: 'These tabs along the bottom are how you move around: Home, Squad, Season, Stats, and History. We’ll visit each one. The highlighted bar is always here when you need it.',
    tab: 'index',
    spotlight: 'tabbar',
  },
  {
    key: 'new-career',
    emoji: '⭐',
    title: 'Start a Career',
    body: 'Every save begins on the New Career screen: pick a franchise and difficulty, then choose how to build your squad. To show you the rest of the app, we’ll set one up now — tap Next and we’ll create a career with a mega draft.',
    route: '/new-career',
    spotlight: 'content',
  },
  {
    key: 'draft',
    emoji: '📋',
    title: 'The Mega Draft',
    body: 'Here’s your draft. You build a 25-player squad pick by pick — snake order, every franchise competing, max 9 overseas. Draft manually, autodraft one pick, or let the CPU finish. Filter by role and nation to find gems.',
    tab: 'season',
    spotlight: 'content',
    ensureCareer: true,
  },
  {
    key: 'squad',
    emoji: '🧢',
    title: 'Build Your Squad: Starting XI',
    body: 'This is the Squad tab’s Starting XI screen. Tap a slot to swap a player, set your Impact Sub, and arrange the batting order — or tap “Autofill” for smart defaults. The other sub-tabs cover your full roster, the bowling plan, and leadership.',
    tab: 'squad',
    spotlight: 'content',
    squadTab: 'batting',
    fillSquad: true,
  },
  {
    key: 'season',
    emoji: '🎮',
    title: 'Play the Season',
    body: 'The Season tab runs your fixtures. Quick-sim a match day for instant results, or enter the Match Centre to play it live. Watch the points table climb toward the playoffs.',
    tab: 'season',
    spotlight: 'content',
  },
  {
    key: 'match-hub',
    emoji: '🏟️',
    title: 'The Match Centre',
    body: 'Live match days happen here: call the toss, confirm your lineup, set aggression, and bring on your Impact Sub at the break — all ball by ball. Your saved squad presets load automatically.',
    tab: 'season',
    spotlight: 'content',
  },
  {
    key: 'stats',
    emoji: '📊',
    title: 'Track Everything',
    body: 'The Stats tab has the full points table, the Orange/Purple Cap races, and the MVP leaderboard. Tap any player to see their season card.',
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
    body: 'That’s the whole loop: draft, manage, play, repeat. Start a New Career from the Home tab whenever you’re ready. You can replay this tour any time from the account menu.',
    tab: 'index',
    spotlight: 'screen',
  },
];

/**
 * Legacy alias kept so any import of TUTORIAL_SLIDES / TutorialSlide keeps
 * working. The guided tour uses TUTORIAL_STEPS.
 */
export type TutorialSlide = TutorialStep;
export const TUTORIAL_SLIDES = TUTORIAL_STEPS;
