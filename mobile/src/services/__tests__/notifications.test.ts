import { IDLE_REMINDER_DAYS, planReminders } from '../notifications';

const DAY = 24 * 60 * 60;
const on = { permissionGranted: true, enabled: true };

describe('planReminders', () => {
  it('schedules nothing without OS permission', () => {
    expect(planReminders({ activePhase: 'season', permissionGranted: false, enabled: true })).toEqual([]);
  });

  it('schedules nothing when the user has opted out', () => {
    expect(planReminders({ activePhase: 'season', permissionGranted: true, enabled: false })).toEqual([]);
  });

  it('schedules nothing without an active career', () => {
    expect(planReminders({ activePhase: null, ...on })).toEqual([]);
  });

  it('reminds about a season in progress after the idle window', () => {
    const plan = planReminders({ activePhase: 'season', ...on });
    expect(plan).toHaveLength(1);
    expect(plan[0].kind).toBe('season_waiting');
    expect(plan[0].delaySeconds).toBe(IDLE_REMINDER_DAYS * DAY);
  });

  it('reminds about an open transfer/retention window', () => {
    const plan = planReminders({ activePhase: 'retention', ...on });
    expect(plan).toHaveLength(1);
    expect(plan[0].kind).toBe('transfer_window');
  });

  it('does not nag once the league is complete', () => {
    expect(planReminders({ activePhase: 'league_complete', ...on })).toEqual([]);
  });

  it('treats playoffs as a season still in progress', () => {
    const plan = planReminders({ activePhase: 'playoffs', ...on });
    expect(plan[0]?.kind).toBe('season_waiting');
  });
});
