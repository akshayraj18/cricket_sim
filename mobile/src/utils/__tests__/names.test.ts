import { abbreviateDismissal, abbreviateName } from '../names';

describe('abbreviateName', () => {
  it('shortens a two-part name to "F. Last"', () => {
    expect(abbreviateName('Jasprit Bumrah')).toBe('J. Bumrah');
    expect(abbreviateName('Sanju Samson')).toBe('S. Samson');
  });

  it('keeps a single-word name as-is', () => {
    expect(abbreviateName('Pant')).toBe('Pant');
  });

  it('keeps a multi-word surname whole', () => {
    expect(abbreviateName('AB de Villiers')).toBe('A. de Villiers');
  });

  it('handles empty / whitespace gracefully', () => {
    expect(abbreviateName('')).toBe('');
    expect(abbreviateName('   ')).toBe('');
  });
});

describe('abbreviateDismissal', () => {
  it('abbreviates caught dismissals', () => {
    expect(abbreviateDismissal('c Sanju Samson b Jasprit Bumrah')).toBe('c S. Samson b J. Bumrah');
  });

  it('abbreviates stumped dismissals', () => {
    expect(abbreviateDismissal('st KL Rahul b Rashid Khan')).toBe('st K. Rahul b R. Khan');
  });

  it('abbreviates bowled and lbw', () => {
    expect(abbreviateDismissal('b Jasprit Bumrah')).toBe('b J. Bumrah');
    expect(abbreviateDismissal('lbw b Rashid Khan')).toBe('lbw b R. Khan');
  });

  it('abbreviates the fielder in a run out', () => {
    expect(abbreviateDismissal('run out (Virat Kohli)')).toBe('run out (V. Kohli)');
    expect(abbreviateDismissal('run out (Virat Kohli/MS Dhoni)')).toBe('run out (V. Kohli/M. Dhoni)');
  });

  it('leaves statuses untouched', () => {
    expect(abbreviateDismissal('not out')).toBe('not out');
    expect(abbreviateDismissal('did not bat')).toBe('did not bat');
    expect(abbreviateDismissal('')).toBe('');
  });
});
