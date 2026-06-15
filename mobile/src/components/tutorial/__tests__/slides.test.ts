import { TUTORIAL_SLIDES } from '../slides';

describe('TUTORIAL_SLIDES', () => {
  it('covers each primary app area in order', () => {
    expect(TUTORIAL_SLIDES.map((s) => s.key)).toEqual([
      'welcome',
      'create',
      'squad',
      'play',
      'stats',
      'save',
    ]);
  });

  it('has unique keys', () => {
    const keys = TUTORIAL_SLIDES.map((s) => s.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it('every slide has an emoji, title, and body', () => {
    for (const slide of TUTORIAL_SLIDES) {
      expect(slide.emoji).toBeTruthy();
      expect(slide.title).toBeTruthy();
      expect(slide.body.length).toBeGreaterThan(10);
    }
  });
});
