import { TUTORIAL_STEPS } from '../slides';

describe('TUTORIAL_STEPS', () => {
  it('covers each primary app area in order', () => {
    expect(TUTORIAL_STEPS.map((s) => s.key)).toEqual([
      'welcome',
      'home',
      'new-career',
      'draft',
      'squad',
      'season',
      'match-hub',
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

  it('drives a career: ensures one before the draft and fills the squad before Starting XI', () => {
    const draft = TUTORIAL_STEPS.find((s) => s.key === 'draft');
    const squad = TUTORIAL_STEPS.find((s) => s.key === 'squad');
    // The draft step opens a career + draft; the squad step finishes the draft
    // and opens the Starting XI sub-tab so those screens have real data.
    expect(draft?.ensureCareer).toBe(true);
    expect(squad?.fillSquad).toBe(true);
    expect(squad?.squadTab).toBe('batting');
    // fillSquad must come after ensureCareer in the flow.
    expect(TUTORIAL_STEPS.indexOf(squad!)).toBeGreaterThan(TUTORIAL_STEPS.indexOf(draft!));
  });
});
