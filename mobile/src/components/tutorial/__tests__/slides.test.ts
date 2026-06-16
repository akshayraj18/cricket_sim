import { TUTORIAL_STEPS } from '../slides';

describe('TUTORIAL_STEPS', () => {
  it('covers each primary app area in order', () => {
    expect(TUTORIAL_STEPS.map((s) => s.key)).toEqual([
      'welcome',
      'home',
      'tabbar',
      'draft',
      'squad',
      'season',
      'stats',
      'history',
      'done',
    ]);
  });

  it('has unique keys', () => {
    const keys = TUTORIAL_STEPS.map((s) => s.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it('every step has an emoji, title, and body', () => {
    for (const step of TUTORIAL_STEPS) {
      expect(step.emoji).toBeTruthy();
      expect(step.title).toBeTruthy();
      expect(step.body.length).toBeGreaterThan(10);
    }
  });

  it('every step that targets a tab uses a real tab name', () => {
    const validTabs = new Set(['index', 'squad', 'season', 'stats', 'history']);
    for (const step of TUTORIAL_STEPS) {
      if (step.tab) expect(validTabs.has(step.tab)).toBe(true);
    }
  });

  it('every step uses a known spotlight region', () => {
    const validSpots = new Set(['tabbar', 'header', 'content', 'screen', undefined]);
    for (const step of TUTORIAL_STEPS) {
      expect(validSpots.has(step.spotlight)).toBe(true);
    }
  });

  it('opens the Starting XI sub-tab on the squad step', () => {
    const squad = TUTORIAL_STEPS.find((s) => s.key === 'squad');
    expect(squad?.tab).toBe('squad');
    expect(squad?.squadTab).toBe('batting');
  });
});
