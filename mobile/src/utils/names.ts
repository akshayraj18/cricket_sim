/**
 * Compact player-name formatting for space-constrained scorecards (in-match
 * batting/bowling cards and recent-match scorecards). Full names are kept
 * everywhere else (the top scoreboard, recent-overs commentary, squad lists).
 */

/**
 * Abbreviate a full name to "F. Last" — first initial + surname. Multi-word
 * surnames are kept whole ("AB de Vylliers" → "A. de Vylliers"); single-word
 * names are returned as-is ("Pent" → "Pent").
 */
export function abbreviateName(full: string): string {
  const name = full.trim();
  if (!name) return name;
  const parts = name.split(/\s+/);
  if (parts.length === 1) return parts[0];
  const [first, ...rest] = parts;
  return `${first[0]}. ${rest.join(' ')}`;
}

/**
 * Abbreviate the names inside a dismissal string so it fits on a card, e.g.
 * "c Senju Semson b Jesprit Bomrah" → "c S. Semson b J. Bomrah",
 * "st KL Rehul b Reshid Khen"       → "st K. Rehul b R. Khen",
 * "lbw b Reshid Khen"               → "lbw b R. Khen",
 * "b Jesprit Bomrah"                → "b J. Bomrah",
 * "run out (Vyrat Kuhli)"           → "run out (V. Kuhli)".
 * Connectives (c / b / st / lbw / run out) and statuses (not out, did not bat)
 * are left untouched.
 */
export function abbreviateDismissal(dismissal: string): string {
  const text = dismissal.trim();
  if (!text) return text;

  // run out (Fielder[/Fielder]) — abbreviate each fielder inside the parens.
  const runOut = text.match(/^run out \((.+)\)$/i);
  if (runOut) {
    const fielders = runOut[1]
      .split('/')
      .map((f) => abbreviateName(f.trim()))
      .join('/');
    return `run out (${fielders})`;
  }

  // "c <fielder> b <bowler>" — caught.
  const caught = text.match(/^c\s+(.+?)\s+b\s+(.+)$/i);
  if (caught) return `c ${abbreviateName(caught[1])} b ${abbreviateName(caught[2])}`;

  // "st <keeper> b <bowler>" — stumped.
  const stumped = text.match(/^st\s+(.+?)\s+b\s+(.+)$/i);
  if (stumped) return `st ${abbreviateName(stumped[1])} b ${abbreviateName(stumped[2])}`;

  // "lbw b <bowler>".
  const lbw = text.match(/^lbw\s+b\s+(.+)$/i);
  if (lbw) return `lbw b ${abbreviateName(lbw[1])}`;

  // "b <bowler>" — bowled.
  const bowled = text.match(/^b\s+(.+)$/i);
  if (bowled) return `b ${abbreviateName(bowled[1])}`;

  // Anything else (e.g. "not out", "did not bat", "retired hurt") — leave as-is.
  return text;
}
