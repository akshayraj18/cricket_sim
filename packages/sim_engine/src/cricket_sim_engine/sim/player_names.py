"""User-supplied player names, applied to newly created careers.

The app ships deliberately fictional player names (see tools/ip_safe_rename.py).
This lets a user substitute their own — most obviously the real ones — by
exporting a two-column CSV, editing the `name` column, and importing it back.

Scope is deliberate and worth stating plainly: overrides are stored against the
USER and applied when a career is CREATED. They cannot retroactively rename a
career that already exists, because a career's names are baked into its saved
state the moment it is drafted — they appear in saved lineups, leadership and
every archived scorecard. Renaming those safely is `LeagueState.rename_player`'s
job, one career at a time; this module is the "set it once, every new career
uses it" half.

`player_key` is the name as shipped. It is stable because we control the data
files, and the rename tool keeps them consistent — so a user's file keeps
working across app updates unless a player is removed from the pools.
"""
from __future__ import annotations

import csv
import io

from cricket_sim_engine import players_data

CSV_COLUMNS = ["player_key", "name"]

MAX_ROWS = 5000
MAX_BYTES = 500_000
MAX_NAME_LENGTH = 60


class NameImportError(ValueError):
    """Raised when a names file is rejected. `errors` lists every problem."""

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors[:5]) + ("; ..." if len(self.errors) > 5 else ""))


def all_pool_names() -> list[str]:
    """Every distinct player name a career could ever draw, sorted.

    Covers the IPL pool, all three all-time pools and the international squads,
    because which of them a user meets depends on the career they start.
    """
    names: set[str] = set()
    for loader in (
        players_data.get_initial_player_pool,
        players_data.get_alltime_player_pool,
        players_data.get_alltime_odi_pool,
        players_data.get_alltime_test_pool,
        players_data.get_alltime_t20_intl_pool,
    ):
        names.update(p.name for p in loader())

    for match_format in ("t20", "odi", "test"):
        rosters, leftover = players_data.get_international_rosters(match_format)
        for squad in rosters.values():
            names.update(p.name for p in squad)
        names.update(p.name for p in (leftover or []))

    return sorted(names)


def export_names_csv(overrides: dict[str, str] | None = None) -> str:
    """Two columns: the shipped name, and what to call the player.

    Any override already saved is pre-filled in `name`, so an export is always a
    faithful picture of the user's current setup and can be re-imported as-is.
    """
    overrides = overrides or {}
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\r\n")
    writer.writeheader()
    for key in all_pool_names():
        writer.writerow({"player_key": key, "name": overrides.get(key, key)})
    return buf.getvalue()


def parse_names_csv(text: str) -> dict[str, str]:
    """Validate a names file and return only the rows that actually rename.

    Rows left at the shipped name are dropped rather than stored, so the saved
    override set stays the size of what the user actually changed instead of
    ~900 identity mappings.

    Validates everything before returning, and reports every problem at once so
    one round trip is enough to fix the file.
    """
    if not text or not text.strip():
        raise NameImportError(["File is empty."])
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise NameImportError([f"File is larger than {MAX_BYTES // 1000}KB."])

    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames:
        raise NameImportError(["File is empty."])
    missing = [c for c in CSV_COLUMNS if c not in reader.fieldnames]
    if missing:
        raise NameImportError([f"Missing column(s): {', '.join(missing)}"])

    known = set(all_pool_names())
    errors: list[str] = []
    seen: set[str] = set()
    overrides: dict[str, str] = {}

    for row_no, row in enumerate(reader, start=2):
        if row_no - 1 > MAX_ROWS:
            errors.append(f"File has more than {MAX_ROWS} rows.")
            break
        if not any((v or "").strip() for v in row.values()):
            continue

        key = (row.get("player_key") or "").strip()
        name = (row.get("name") or "").strip()
        if not key:
            errors.append(f"row {row_no}: player_key is blank")
            continue
        if key in seen:
            errors.append(f"row {row_no}: player_key {key!r} appears more than once")
            continue
        seen.add(key)
        if key not in known:
            errors.append(
                f"row {row_no}: {key!r} is not a player in this game — "
                "player_key must not be edited"
            )
            continue
        if not name:
            errors.append(f"row {row_no}: name is blank")
            continue
        if len(name) > MAX_NAME_LENGTH:
            errors.append(f"row {row_no}: name is longer than {MAX_NAME_LENGTH} characters")
            continue
        if name != key:
            overrides[key] = name

    # Two players sharing a name would break the roster, whose identity IS the
    # name — the draft, lineups and scorecards all key off it.
    final: dict[str, str] = {k: overrides.get(k, k) for k in known}
    used: dict[str, list[str]] = {}
    for key, name in final.items():
        used.setdefault(name, []).append(key)
    for name, keys in sorted(used.items()):
        if len(keys) > 1:
            errors.append(f"name {name!r} would be used by {len(keys)} players: {', '.join(sorted(keys)[:3])}")

    if errors:
        raise NameImportError(errors)
    return overrides


def apply_name_overrides(league, overrides: dict[str, str] | None) -> int:
    """Rename players in a freshly created `league`. Returns how many changed.

    Safe to assign `player.name` directly here, unlike a mid-career rename: a
    career being created has no saved lineups, leadership or match history
    referring to the old name yet. Applied to rosters AND the free-agent pool,
    so a name is consistent whether the player was drafted or not.
    """
    if not overrides:
        return 0
    changed = 0
    players = [p for team in league.teams for p in team.roster]
    players += list(getattr(league, "player_pool", None) or [])
    for player in players:
        new_name = overrides.get(player.name)
        if new_name and new_name != player.name:
            player.name = new_name
            changed += 1
    return changed
