import { funnelEventsFor, type FunnelContext, type FunnelSnapshot } from '../use-funnel-tracking';

const context: FunnelContext = {
  competition: 'ipl',
  match_format: 't20',
  career_mode: 'league',
  draft_type: 'mega',
  season: 2026,
};

const base: FunnelSnapshot = {
  careerId: 'career-1',
  phase: 'draft',
  draftStarted: false,
  matchesPlayed: 0,
  liveMatchStatus: null,
  completedSeasons: 0,
};

const at = (over: Partial<FunnelSnapshot>): FunnelSnapshot => ({ ...base, ...over });
const names = (prev: FunnelSnapshot | null, cur: FunnelSnapshot) =>
  funnelEventsFor(prev, cur, context).map((e) => e.event);

describe('funnelEventsFor — guards against forged events', () => {
  it('emits nothing on the first observation of a career', () => {
    // A cold start into a career that is already mid-season is not a user
    // finishing a draft. Without this, every app open would forge events.
    expect(names(null, at({ phase: 'season', draftStarted: true, matchesPlayed: 40 }))).toEqual([]);
  });

  it('emits nothing when the career changed underneath us', () => {
    const prev = at({ careerId: 'career-1', phase: 'draft' });
    const next = at({ careerId: 'career-2', phase: 'season', draftStarted: true });
    expect(names(prev, next)).toEqual([]);
  });

  it('emits nothing when the payload is unchanged', () => {
    // The payload refetches on every tab focus, so an unchanged snapshot must
    // be silent or a single draft would report dozens of completions.
    const snap = at({ phase: 'season', draftStarted: true, matchesPlayed: 12 });
    expect(names(snap, snap)).toEqual([]);
  });
});

describe('funnelEventsFor — draft', () => {
  it('reports the draft starting', () => {
    expect(names(at({ draftStarted: false }), at({ draftStarted: true }))).toContain('draft_started');
  });

  it('reports the draft completing when the phase leaves draft', () => {
    const prev = at({ phase: 'draft', draftStarted: true });
    const next = at({ phase: 'season', draftStarted: true });
    expect(names(prev, next)).toContain('draft_completed');
  });

  it('reports completion regardless of how the draft ended', () => {
    // Autodraft jumps straight from an unstarted draft to an open season; the
    // last manual pick walks there. Both must count, which is the whole reason
    // this is derived from the payload instead of from button handlers.
    const autodrafted = names(at({ phase: 'draft', draftStarted: false }), at({ phase: 'season', draftStarted: true }));
    expect(autodrafted).toEqual(expect.arrayContaining(['draft_started', 'draft_completed']));
  });

  it('does not re-report a completed draft on later refreshes', () => {
    const inSeason = at({ phase: 'season', draftStarted: true });
    expect(names(inSeason, inSeason)).not.toContain('draft_completed');
  });
});

describe('funnelEventsFor — matches', () => {
  it('marks the user finishing their own match as live', () => {
    const prev = at({ phase: 'season', matchesPlayed: 3, liveMatchStatus: 'over' });
    const next = at({ phase: 'season', matchesPlayed: 4, liveMatchStatus: 'complete' });
    const [event] = funnelEventsFor(prev, next, context).filter((e) => e.event === 'match_played');
    expect(event.props).toMatchObject({ mode: 'live', matches: 1 });
  });

  it('marks a simulated round as quick_sim and reports how many matches', () => {
    const prev = at({ phase: 'season', matchesPlayed: 0, liveMatchStatus: null });
    const next = at({ phase: 'season', matchesPlayed: 5, liveMatchStatus: null });
    const [event] = funnelEventsFor(prev, next, context).filter((e) => e.event === 'match_played');
    expect(event.props).toMatchObject({ mode: 'quick_sim', matches: 5 });
  });

  it('does not report a match when the count is unchanged', () => {
    const snap = at({ phase: 'season', matchesPlayed: 7, liveMatchStatus: 'complete' });
    expect(names(snap, snap)).not.toContain('match_played');
  });

  it('does not report a match when the log shrinks at a new season', () => {
    // match_log resets between seasons; a negative delta is not gameplay.
    const prev = at({ phase: 'season_end', matchesPlayed: 14 });
    const next = at({ phase: 'season', matchesPlayed: 0 });
    expect(names(prev, next)).not.toContain('match_played');
  });
});

describe('funnelEventsFor — season progress', () => {
  it('reports reaching the playoffs once', () => {
    expect(names(at({ phase: 'league_complete' }), at({ phase: 'playoffs' }))).toContain('playoffs_reached');
    expect(names(at({ phase: 'playoffs' }), at({ phase: 'playoffs' }))).not.toContain('playoffs_reached');
  });

  it('reports a completed season when the counter increases', () => {
    const prev = at({ phase: 'playoffs', completedSeasons: 0 });
    const next = at({ phase: 'season_end', completedSeasons: 1 });
    const [event] = funnelEventsFor(prev, next, context).filter((e) => e.event === 'season_completed');
    expect(event.props).toMatchObject({ completed_seasons: 1 });
  });

  it('keys season completion off the counter, not the phase', () => {
    // Sitting on season_end across refreshes must not keep reporting.
    const parked = at({ phase: 'season_end', completedSeasons: 3 });
    expect(names(parked, parked)).not.toContain('season_completed');
  });
});

describe('funnelEventsFor — segmentation', () => {
  it('tags every event with competition, format and career mode', () => {
    const events = funnelEventsFor(
      at({ phase: 'draft', draftStarted: true }),
      at({ phase: 'season', draftStarted: true, matchesPlayed: 5 }),
      { ...context, competition: 'international', match_format: 'test', career_mode: 'bilateral' }
    );
    expect(events.length).toBeGreaterThan(0);
    for (const e of events) {
      expect(e.props).toMatchObject({
        competition: 'international',
        match_format: 'test',
        career_mode: 'bilateral',
      });
    }
  });
});
