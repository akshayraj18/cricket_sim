# Player names via CSV

**Shipped 2026-08-20.** Users substitute their own player names — most obviously
the real ones — by exporting a two-column CSV, editing it in a spreadsheet, and
importing it back. Lives in Settings (the account sheet).

This supersedes an earlier per-career design that also carried ratings; see
"What changed and why" at the end.

---

## Scope, stated plainly

Overrides are stored **against the user** and applied when a career is
**created**. They do not retroactively rename a career that already exists.

That is a deliberate boundary, not an oversight. A career's names are baked into
its saved state the moment it is drafted — they appear in saved lineups,
leadership, and every archived scorecard. Rewriting those safely is
`LeagueState.rename_player`'s job, one career at a time, and it is not something
a settings screen should do to every career at once.

The UI says so directly ("Applies to new careers"), because *"I renamed everyone
and nothing changed"* is the obvious way to be confused by this. A backend test
asserts an existing career is untouched, so the limitation cannot quietly
regress into a surprise.

## Format

Two columns, ~900 rows — every distinct name across every pool a career could
draw from (IPL, all three all-time pools, and the international squads), because
which of them a user meets depends on the career they start.

| Column | Editable | Notes |
|---|---|---|
| `player_key` | **no** | the name as shipped; how a row is matched |
| `name` | yes | what to call the player |

`player_key` is stable because we control the data files and
`tools/ip_safe_rename.py` keeps them consistent, so a user's file keeps working
across app updates unless a player leaves the pools.

An export pre-fills any override already saved, so it always reflects the user's
current setup and can be re-imported unchanged. **Re-importing an unedited
export is how a user clears everything** — only rows that differ from the
shipped name are stored, so a file with no edits saves nothing.

## Validation

All-or-nothing, and every problem is reported rather than the first, so one
round trip is enough to fix a file. Rejected: unknown or duplicated
`player_key`, blank or overlong names, a missing column, and — most
importantly — **two players ending up with the same name**, including a rename
onto a player the file did not touch. A roster's identity *is* the name; the
draft, lineups and scorecards all key off it.

## Storage

`users.player_name_overrides`, a nullable JSONB column holding `{shipped_name:
user_name}`. A column rather than a table because it is read once per career
creation and never queried across users. Only changed rows are stored, so the
typical row is small rather than ~900 identity mappings. Empty is stored as
NULL so "no overrides" has a single representation.

## Applying

`apply_name_overrides(league, overrides)` runs inside `build_league_state`,
after the league is constructed and before it is persisted. Assigning
`player.name` directly is safe *there specifically*: a career being created has
no saved lineups, leadership or match history referencing the old name yet.
The same assignment mid-career would corrupt a save, which is why the mid-career
path goes through `rename_player`.

Applied to rosters **and** the free-agent pool, so a name looks the same whether
the player was drafted or not. Overrides naming players absent from a given
career are ignored — a user's file spans every pool, any one career holds some.

## Mobile

`expo-sharing` and `expo-document-picker` are **native** modules, loaded with a
guarded `require()` rather than a static import. A static import of a missing
native module throws while the module graph is still loading, before any
component can catch it, which takes down the whole screen — that is exactly how
the home screen died with "Cannot find native module 'ExpoDocumentPicker'" plus
three cascading render errors. Loading on demand contains it to a message.

This matters beyond a stale local build: EAS Update ships JS without rebuilding
native code, so a JS-only update referencing a module the installed binary lacks
would otherwise brick the screen for every user until they updated.

**Adding either module requires `make mobile-prebuild`** — a JS reload will not
pick it up.

---

## What changed and why

The first implementation exported a career's whole roster including ratings,
role, age and archetype, and imported it back into that career. It worked and
was fully tested, but was replaced because:

- **Names-only removes the balance problem.** Editable ratings meant a career
  could be arbitrarily strong, which would have had to be flagged and excluded
  from any future leaderboard. With names only, there is nothing to exclude.
- **It removes most of the validation surface.** Ratings, ages, slots and four
  separate enums each needed range and vocabulary checks, and the enums are
  inconsistent in the shipped data (`"Death"` and `"Death Overs"`,
  `"Middle-order"` and `"Middle-over Rotator"`) — so the validator had to accept
  synonyms or reject the app's own export.
- **Per-career meant picking a career first.** Setting names once, for every
  future career, matches how someone actually wants to use this.

One useful thing was learned from the discarded version and is worth keeping in
mind: its round-trip test (export → import changes nothing) immediately caught a
shipped player aged **14**, below an age floor that had been assumed rather than
measured. Bounds and vocabularies should be derived from the data, not guessed.
