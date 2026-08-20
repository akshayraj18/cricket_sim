"""CSV export/import for a career's whole-league roster.

Lets a user export every player in their career, edit names and ratings in a
spreadsheet, and import the file back. See docs/CSV_ROSTER_IO.md for the design;
the essentials that shape this module:

- `Player` has no id. Its identity is its name, which is unique within a career
  (`rename_player` refuses a duplicate). So export writes the current name as a
  separate do-not-edit `player_key` column and import matches on that, leaving
  `name` free to be edited. Matching on `name` alone would break in exactly the
  case the feature exists for.
- A name change must go through `LeagueState.rename_player`, which also rewrites
  the name across saved presets, leadership and serialised match history. Setting
  `player.name` directly leaves a career whose scorecards reference a player who
  no longer exists.
- Validation is all-or-nothing. A half-applied import leaves a career the user
  cannot reason about, so nothing is written until every row passes.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

# Column order as exported. Import tolerates a different order (spreadsheets
# reorder columns) but requires these names.
CSV_COLUMNS = [
    "player_key",
    "team",
    "name",
    "role",
    "base_ovr",
    "batting_ovr",
    "bowling_ovr",
    "is_overseas",
    "age",
    "batting_hand",
    "bowling_hand",
    "batting_archetype",
    "bowling_phase",
    "bowling_type",
    "strengths",
    "weaknesses",
    "natural_slot",
]

EDITABLE = {c for c in CSV_COLUMNS} - {"player_key", "team"}

# Team label used for players who are not on a roster (the free-agent pool).
FREE_AGENT = "(free agent)"

# Accepted enum values.
#
# These are the union of what the shipped pools actually contain, not a tidied
# ideal: the data carries synonyms ("Death" and "Death Overs", "Middle-order"
# and "Middle-over Rotator", "New Ball" and "New-ball Bowler"). Narrowing them
# here would make the app reject its own exported file, so the round-trip is
# guarded by a test over every shipped player rather than by tightening this.
ROLES = {"All-Rounder", "Batsman", "Bowler (Fast)", "Bowler (Spin)", "Wicketkeeper"}
BATTING_ARCHETYPES = {
    "Aggressive Opener", "Aggressor", "Anchor", "Defensive Tailender", "Finisher",
    "Lower-order Hitter", "Middle-order Rotator", "Middle-over Rotator",
}
BOWLING_PHASES = {
    "Death", "Death Overs", "Flexible", "Middle Overs", "New Ball",
    "New-ball Bowler", "Part-time", "Powerplay",
}
BATTING_HANDS = {"Left", "Right"}
BOWLING_HANDS = {"Left", "Right", "Both", "None"}

RATING_RANGE = (0, 100)
# Widened to 14 because the shipped pools contain a 14-year-old (all-time greats
# are stored at their prime age, and the youngest debutants qualify). A floor of
# 15 rejected the app's own export — caught by the round-trip test, which is the
# reason these bounds are measured against the data rather than assumed.
AGE_RANGE = (14, 50)
SLOT_RANGE = (1, 11)

# Guards against a mistaken or hostile upload. A career holds ~340 players.
MAX_ROWS = 1000
MAX_BYTES = 1_000_000


class RosterImportError(ValueError):
    """Raised when an import is rejected. `errors` lists every problem found."""

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors[:5]) + ("; ..." if len(self.errors) > 5 else ""))


@dataclass
class ImportReport:
    renamed: int = 0
    rerated: int = 0
    unchanged: int = 0
    ignored_team_changes: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self):
        return {
            "renamed": self.renamed,
            "rerated": self.rerated,
            "unchanged": self.unchanged,
            "ignored_team_changes": self.ignored_team_changes,
            "errors": list(self.errors),
        }


def _all_players(league):
    """(team_label, player) for every player in the career, rosters then pool."""
    for team in league.teams:
        for player in team.roster:
            yield team.name, player
    for player in getattr(league, "player_pool", []) or []:
        yield FREE_AGENT, player


def _row_for(team_label, player):
    return {
        "player_key": player.name,
        "team": team_label,
        "name": player.name,
        "role": player.role,
        "base_ovr": player.base_ovr,
        "batting_ovr": player.batting_ovr,
        "bowling_ovr": player.bowling_ovr,
        "is_overseas": player.is_overseas,
        "age": player.age,
        "batting_hand": player.batting_hand,
        "bowling_hand": player.bowling_hand,
        "batting_archetype": player.batting_archetype,
        "bowling_phase": player.bowling_phase,
        "bowling_type": player.bowling_type,
        "strengths": player.strengths,
        "weaknesses": player.weaknesses,
        "natural_slot": getattr(player, "preferred_position", "") or "",
    }


def export_roster_csv(league) -> str:
    """Serialise every player in `league` to CSV text.

    Season statistics are deliberately excluded: they are match-derived, and a
    user editing them would desynchronise the career from its own history.
    """
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\r\n")
    writer.writeheader()
    for team_label, player in _all_players(league):
        writer.writerow(_row_for(team_label, player))
    return buf.getvalue()


def _parse_int(raw, label, lo, hi, errors, row_no):
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        errors.append(f"row {row_no}: {label} must be a whole number, got {raw!r}")
        return None
    if not (lo <= value <= hi):
        errors.append(f"row {row_no}: {label} must be between {lo} and {hi}, got {value}")
        return None
    return value


def _parse_bool(raw, label, errors, row_no):
    text = str(raw).strip().lower()
    if text in ("true", "1", "yes"):
        return True
    if text in ("false", "0", "no"):
        return False
    errors.append(f"row {row_no}: {label} must be True or False, got {raw!r}")
    return None


def _parse_enum(raw, label, allowed, errors, row_no):
    text = str(raw).strip()
    if text not in allowed:
        errors.append(f"row {row_no}: {label} {text!r} is not a recognised value")
        return None
    return text


def import_roster_csv(league, text: str) -> ImportReport:
    """Apply an edited roster CSV to `league`.

    Validates the whole file first and raises `RosterImportError` without
    touching the career if anything is wrong. Rows may be omitted: a player not
    present in the file is simply left alone, so a user can export everything
    and send back only the rows they changed.
    """
    if text is None:
        raise RosterImportError(["No file contents."])
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise RosterImportError([f"File is larger than {MAX_BYTES // 1000}KB."])

    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames:
        raise RosterImportError(["File is empty."])
    missing = [c for c in CSV_COLUMNS if c not in reader.fieldnames]
    if missing:
        raise RosterImportError([f"Missing column(s): {', '.join(missing)}"])

    by_key = {player.name: player for _, player in _all_players(league)}
    errors: list[str] = []
    seen_keys: set[str] = set()
    # key -> validated field values to apply
    planned: dict[str, dict] = {}
    ignored_team_changes = 0

    for row_no, row in enumerate(reader, start=2):  # row 1 is the header
        if row_no - 1 > MAX_ROWS:
            errors.append(f"File has more than {MAX_ROWS} rows.")
            break
        if not any((v or "").strip() for v in row.values()):
            continue  # blank line

        key = (row.get("player_key") or "").strip()
        if not key:
            errors.append(f"row {row_no}: player_key is blank")
            continue
        if key in seen_keys:
            errors.append(f"row {row_no}: player_key {key!r} appears more than once")
            continue
        seen_keys.add(key)
        if key not in by_key:
            errors.append(
                f"row {row_no}: no player named {key!r} in this career — "
                "player_key must not be edited; re-export and try again"
            )
            continue

        new_name = (row.get("name") or "").strip()
        if not new_name:
            errors.append(f"row {row_no}: name is blank")
            continue

        values = {
            "name": new_name,
            "role": _parse_enum(row.get("role"), "role", ROLES, errors, row_no),
            "base_ovr": _parse_int(row.get("base_ovr"), "base_ovr", *RATING_RANGE, errors, row_no),
            "batting_ovr": _parse_int(row.get("batting_ovr"), "batting_ovr", *RATING_RANGE, errors, row_no),
            "bowling_ovr": _parse_int(row.get("bowling_ovr"), "bowling_ovr", *RATING_RANGE, errors, row_no),
            "is_overseas": _parse_bool(row.get("is_overseas"), "is_overseas", errors, row_no),
            "age": _parse_int(row.get("age"), "age", *AGE_RANGE, errors, row_no),
            "batting_hand": _parse_enum(row.get("batting_hand"), "batting_hand", BATTING_HANDS, errors, row_no),
            "bowling_hand": _parse_enum(row.get("bowling_hand"), "bowling_hand", BOWLING_HANDS, errors, row_no),
            "batting_archetype": _parse_enum(
                row.get("batting_archetype"), "batting_archetype", BATTING_ARCHETYPES, errors, row_no
            ),
            "bowling_phase": _parse_enum(
                row.get("bowling_phase"), "bowling_phase", BOWLING_PHASES, errors, row_no
            ),
            "bowling_type": (row.get("bowling_type") or "").strip(),
            "strengths": (row.get("strengths") or "").strip(),
            "weaknesses": (row.get("weaknesses") or "").strip(),
            "natural_slot": _parse_int(row.get("natural_slot"), "natural_slot", *SLOT_RANGE, errors, row_no),
        }
        if (row.get("team") or "").strip() != _team_label_of(league, by_key[key]):
            # Moving players between teams would have to re-check squad size and
            # overseas limits, so it is out of scope; say so rather than silently
            # appearing to accept it.
            ignored_team_changes += 1
        planned[key] = values

    # Final names must stay unique across the WHOLE career, including players
    # the file did not mention.
    final_names: dict[str, str] = {}
    for name in by_key:
        final_names[name] = planned[name]["name"] if name in planned else name
    collisions: dict[str, list[str]] = {}
    for key, final in final_names.items():
        collisions.setdefault(final, []).append(key)
    for final, keys in collisions.items():
        if len(keys) > 1:
            errors.append(f"name {final!r} would be used by {len(keys)} players: {', '.join(sorted(keys))}")

    if errors:
        raise RosterImportError(errors)

    return _apply(league, by_key, planned, ignored_team_changes)


def _team_label_of(league, player):
    for team in league.teams:
        if any(p is player for p in team.roster):
            return team.name
    return FREE_AGENT


def _apply(league, by_key, planned, ignored_team_changes) -> ImportReport:
    report = ImportReport(ignored_team_changes=ignored_team_changes)

    renames = {k: v["name"] for k, v in planned.items() if v["name"] != k}
    # Two-phase, because renaming A->B while B still exists is rejected by
    # rename_player. Swapping two names is a legitimate edit and would otherwise
    # fail with a confusing "another player already has that name".
    if renames:
        placeholders = {}
        for i, key in enumerate(renames):
            placeholder = f"__csv_import_{i}__"
            league.rename_player(key, placeholder)
            placeholders[placeholder] = renames[key]
        for placeholder, final in placeholders.items():
            league.rename_player(placeholder, final)
        report.renamed = len(renames)

    for key, values in planned.items():
        player = by_key[key]
        changed = False
        for attr in (
            "role", "base_ovr", "batting_ovr", "bowling_ovr", "is_overseas", "age",
            "batting_hand", "bowling_hand", "batting_archetype", "bowling_phase",
            "bowling_type", "strengths", "weaknesses",
        ):
            if getattr(player, attr) != values[attr]:
                setattr(player, attr, values[attr])
                changed = True
        if getattr(player, "preferred_position", None) != values["natural_slot"]:
            player.preferred_position = values["natural_slot"]
            changed = True
        if changed:
            report.rerated += 1
        elif key not in renames:
            report.unchanged += 1

    # Flag the career as edited. Ratings are balance, so if leaderboards or any
    # social feature ever ship these careers must be excludable — and that is
    # impossible to reconstruct after the fact.
    league.roster_modified = True
    return report
