# Design — CSV roster export / import

**Goal:** a user exports their career's roster as a CSV, edits it in a
spreadsheet — their own player names and their own ratings — and imports it
back. Import consumes exactly the format export produces.

**Secondary benefit:** this is also the cleanest answer to the IP question.
`LAUNCH_ROADMAP.md` §0.1 already leans on the in-app roster editor as the
standard workaround; a CSV round-trip makes restoring real names a 30-second
job instead of 340 individual edits, while we continue to *ship* only
fictional names.

---

## 1. The hard part: identity

`Player` has **no ID**. Its identity is `name` (see `models.py` — the
constructor sets `self.name` and nothing stable beside it). Names are unique
within a career: `rename_player()` rejects a name already in use.

So the obvious design — match imported rows to players by name — breaks in
exactly the case the feature exists for. Rename "Vyrat Kuhli" to "Virat Kohli"
in the spreadsheet and there is no longer anything tying that row to the player.

Two ways out:

**Option A — add a real `player_id`.** Generate a stable id per player at career
creation, persist it in `state_blob`, export it, match on it. Correct long-term
and robust against any edit. Costs a model change plus a backfill path for the
48 careers already in production, which have no ids.

**Option B — export the current name as a separate, do-not-edit key column.**
Export writes `player_key` (the name at export time) alongside the editable
`name`. Import matches on `player_key` and treats `name` as the desired value.
No model change; works on existing careers immediately.

**Recommendation: B for v1, A later.** B ships inside the release window and
leans on the uniqueness guarantee that already exists. Its one weakness is that
a `player_key` goes stale if the roster is renamed in-app between export and
import — which is detectable, and should produce a clear "these N rows no longer
match anyone; re-export and try again" error rather than a partial apply.

Do **not** silently fall back to matching on `name` when `player_key` misses.
That reintroduces the original ambiguity and can assign edits to the wrong
player.

## 2. Renames must go through `rename_player()`

`LeagueState.rename_player()` does considerably more than set `p.name`: it
rewrites the name across saved presets, leadership, and the serialised match
history (`_replace_in_obj`, `_deep_rename`). An import that assigns `p.name`
directly would leave a career whose scorecards and saved XI still reference the
old name — corruption that would not surface until the user opened History.

So: **rating edits** may be applied to the `Player` object directly; **name
edits** must call `rename_player()`.

### The swap case

Renaming A→B and B→A in one file is legitimate and will fail if applied
sequentially, because `rename_player()` refuses a name that is currently taken.
Apply renames in two phases: first move every renamed player to a unique
temporary placeholder, then from placeholder to target. Otherwise a user
reordering their squad's names gets an unexplained "another player already has
that name".

## 3. Format

One row per player. Column order matches export; import is tolerant of column
*order* but strict about names, so a spreadsheet that reorders columns still
works.

| Column | Editable | Notes |
|---|---|---|
| `player_key` | **no** | identity. Do not edit. |
| `team` | no (v1) | informational. Changing it does **not** transfer a player — see §6. |
| `name` | yes | the rename field |
| `role` | yes | `All-Rounder`, `Batsman`, `Bowler (Fast)`, `Bowler (Spin)`, `Wicketkeeper` |
| `base_ovr`, `batting_ovr`, `bowling_ovr` | yes | integer 0–100 |
| `age` | yes | integer, 15–45 |
| `is_overseas` | yes | `True` / `False` |
| `batting_hand`, `bowling_hand` | yes | `Left`, `Right` (bowling also `None`) |
| `batting_archetype` | yes | `Aggressive Opener`, `Anchor`, `Defensive Tailender`, `Finisher`, `Lower-order Hitter`, `Middle-over Rotator` |
| `bowling_phase` | yes | `Death Overs`, `Flexible`, `Middle Overs`, `New Ball`, `Part-time` |
| `bowling_type` | yes | free text; `bowling_kind()` classifies spin from it, so typos silently change behaviour — validate against the observed set |
| `strengths`, `weaknesses` | yes | free text, comma-separated inside quotes |
| `natural_slot` | yes | integer 1–11 |

Season statistics are deliberately **not** exported. They are match-derived; a
user editing them would desynchronise the career from its own history.

## 4. Validation — all-or-nothing

Validate the entire file, then apply, or reject with a per-row report. A
half-applied import leaves a career in a state the user cannot reason about.

Reject on: unknown `player_key`; duplicate `player_key`; a resulting `name` that
is blank or collides with another player's final name; any enum value outside
its set; any numeric outside its range; more rows than the career has players.

Enum validation matters more than it looks. `role` drives
`is_bowling_role()`/`counts_as_batter()`, `bowling_type` drives `bowling_kind()`,
and `batting_archetype` feeds `derive_preferred_position()`. A typo'd role does
not error — it quietly changes selection and simulation behaviour.

Partial files are fine: a row omitted simply is not updated. That lets a user
export everything and send back only the ten rows they changed.

## 5. API

Career-scoped, alongside the existing `POST /season/rename`:

```
GET  /careers/{career_id}/roster.csv   -> text/csv
POST /careers/{career_id}/roster.csv   -> multipart or text/csv body
```

The POST returns a structured result: counts of renamed / re-rated / unchanged
rows, plus the rejection list when validation fails. The mobile client shows
that as a confirmation rather than a silent success.

Caps: reject files over ~1 MB or over ~1,000 rows before parsing. A career has
roughly 340 players, so anything larger is either a mistake or an attack.

## 6. Deliberately out of scope for v1

- **Moving players between teams via the `team` column.** Squad size, overseas
  limits and the draft's invariants all constrain team composition; honouring
  arbitrary team edits means re-validating all of it. Export the column for
  context, ignore it on import, and say so in the response.
- **Adding or deleting players.** Rows whose `player_key` is unknown are an
  error, not an insert. Creating players needs squad-size validation.
- **Editing season stats.** See §3.

## 7. Mobile plumbing

`expo-file-system` (~56.0.8) is already installed. **`expo-sharing` and
`expo-document-picker` are not** — both are native modules, so adding them
requires a dev-client rebuild (`make mobile-ios`) and a new EAS build. That is
the main non-obvious cost of this feature; it cannot ship as a JS-only update.

- **Export:** build the CSV, write it to the cache directory, hand it to
  `Sharing.shareAsync()`. On iOS that gives Files / AirDrop / Mail.
- **Import:** `DocumentPicker.getDocumentAsync({ type: 'text/csv' })`, read the
  file, POST it, then show the counts returned by the server.

An escape hatch worth having on day one: allow pasting CSV text into a text box.
It needs no native module, works when the share sheet misbehaves, and makes the
feature testable in the simulator before the native build lands.

## 8. Risks

- **Ratings are balance.** A user maxing every rating is fine in a single-player
  career, but if leaderboards or any social feature ever ship, these careers must
  be excluded. Set a `roster_modified` flag on the career at the first successful
  import — cheap now, effectively impossible to reconstruct later.
- **Round-trip fidelity.** Export → import with no edits must be a no-op. Worth
  an explicit test; it is the cheapest guard against a format drift bug.
- **CRLF.** The shipped CSVs use CRLF and spreadsheets will happily produce
  either. Parse with the `csv` module rather than splitting on `\n`, and never
  round-trip a file with `Path.read_text()`, which rewrites line endings.
