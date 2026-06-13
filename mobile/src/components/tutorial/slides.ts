/**
 * Content for the first-run tutorial carousel. Each slide maps to one primary
 * area of the app. Kept as plain data so the carousel component stays dumb and
 * the copy is easy to tweak. `emoji` is used as a lightweight, theme-agnostic
 * illustration (no asset pipeline needed for Phase 4).
 */
export interface TutorialSlide {
  key: string;
  emoji: string;
  title: string;
  body: string;
}

export const TUTORIAL_SLIDES: TutorialSlide[] = [
  {
    key: 'welcome',
    emoji: '🏏',
    title: 'Welcome to Cric Sim',
    body: 'Take charge of an IPL franchise — draft your squad, set your tactics, and play out a full season. Here’s a 30-second tour.',
  },
  {
    key: 'create',
    emoji: '⭐',
    title: 'Start a Career',
    body: 'Pick a franchise and a difficulty, then choose a draft pool — current 2026 stars, all-time greats, or jump straight in with the real 2026 roster.',
  },
  {
    key: 'squad',
    emoji: '🧢',
    title: 'Build Your Squad',
    body: 'In the Squad tab, set your Starting XI and your Impact Sub, pick a captain, and arrange the batting order. Tap “Autofill” for smart defaults any time.',
  },
  {
    key: 'play',
    emoji: '🎮',
    title: 'Play the Season',
    body: 'From the Season tab, run each match day. Quick-sim for instant results, or jump into the Match Centre to call the toss, confirm your lineup, and make your Impact Sub live.',
  },
  {
    key: 'stats',
    emoji: '📊',
    title: 'Track Everything',
    body: 'The Stats tab has the league table and the MVP race; History keeps every season, champion, and all-time leader you’ve built.',
  },
  {
    key: 'save',
    emoji: '🔒',
    title: 'Keep Your Career Safe',
    body: 'You can play as a guest right away. Link Apple or Google any time from your account menu to back up your career and play across devices.',
  },
];
