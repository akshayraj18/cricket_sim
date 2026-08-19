import { abbreviateDismissal, abbreviateName } from '../names';

describe('abbreviateName', () => {
  it('shortens a two-part name to "F. Last"', () => {
    expect(abbreviateName('Jesprit Bomrah')).toBe('J. Bomrah');
    expect(abbreviateName('Senju Semson')).toBe('S. Semson');
  });

  it('keeps a single-word name as-is', () => {
    expect(abbreviateName('Pent')).toBe('Pent');
  });

  it('keeps a multi-word surname whole', () => {
    expect(abbreviateName('AB de Vylliers')).toBe('A. de Vylliers');
  });

  it('handles empty / whitespace gracefully', () => {
    expect(abbreviateName('')).toBe('');
    expect(abbreviateName('   ')).toBe('');
  });
});

describe('abbreviateDismissal', () => {
  it('abbreviates caught dismissals', () => {
    expect(abbreviateDismissal('c Senju Semson b Jesprit Bomrah')).toBe('c S. Semson b J. Bomrah');
  });

  it('abbreviates stumped dismissals', () => {
    expect(abbreviateDismissal('st KL Rehul b Reshid Khen')).toBe('st K. Rehul b R. Khen');
  });

  it('abbreviates bowled and lbw', () => {
    expect(abbreviateDismissal('b Jesprit Bomrah')).toBe('b J. Bomrah');
    expect(abbreviateDismissal('lbw b Reshid Khen')).toBe('lbw b R. Khen');
  });

  it('abbreviates the fielder in a run out', () => {
    expect(abbreviateDismissal('run out (Vyrat Kuhli)')).toBe('run out (V. Kuhli)');
    expect(abbreviateDismissal('run out (Vyrat Kuhli/MS Dhuni)')).toBe('run out (V. Kuhli/M. Dhuni)');
  });

  it('leaves statuses untouched', () => {
    expect(abbreviateDismissal('not out')).toBe('not out');
    expect(abbreviateDismissal('did not bat')).toBe('did not bat');
    expect(abbreviateDismissal('')).toBe('');
  });
});
