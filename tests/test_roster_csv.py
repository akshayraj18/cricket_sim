"""CSV roster export/import.

The load-bearing property is the round trip: export -> import with no edits must
change nothing. If that ever breaks, every user's file silently stops matching
their career, so it is asserted directly rather than inferred.
"""
import csv
import io

import pytest

from cricket_sim_engine.sim.roster_csv import (
    CSV_COLUMNS,
    FREE_AGENT,
    RosterImportError,
    export_roster_csv,
    import_roster_csv,
)

from .conftest import drafted_league

pytestmark = pytest.mark.integration


def _rows(text):
    return list(csv.DictReader(io.StringIO(text, newline="")))


def _rewrite(text, key, **changes):
    """Return `text` with the row for `key` altered."""
    rows = _rows(text)
    for row in rows:
        if row["player_key"] == key:
            row.update({k: str(v) for k, v in changes.items()})
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def _snapshot(league):
    return {
        p.name: (p.role, p.base_ovr, p.batting_ovr, p.bowling_ovr, p.age,
                 p.batting_archetype, p.bowling_phase, getattr(p, "preferred_position", None))
        for _, p in _all(league)
    }


def _all(league):
    for t in league.teams:
        for p in t.roster:
            yield t.name, p
    for p in league.player_pool or []:
        yield FREE_AGENT, p


# --------------------------------------------------------------------- export

def test_export_covers_every_player_in_the_career():
    league = drafted_league()
    rows = _rows(export_roster_csv(league))
    assert len(rows) == sum(1 for _ in _all(league))
    assert {r["player_key"] for r in rows} == {p.name for _, p in _all(league)}


def test_export_marks_free_agents_with_a_team_label():
    league = drafted_league()
    rows = _rows(export_roster_csv(league))
    labels = {r["team"] for r in rows}
    assert FREE_AGENT in labels, "undrafted players still need a team column value"


def test_export_omits_season_statistics():
    # Stats are match-derived; letting a user edit them desynchronises the
    # career from its own history.
    league = drafted_league()
    header = _rows(export_roster_csv(league))[0].keys()
    for banned in ("runs", "wickets", "catches", "fifties", "stats"):
        assert banned not in header


def test_player_key_matches_name_on_a_fresh_export():
    league = drafted_league()
    for row in _rows(export_roster_csv(league)):
        assert row["player_key"] == row["name"]


# ----------------------------------------------------------------- round trip

def test_round_trip_with_no_edits_changes_nothing():
    league = drafted_league()
    before = _snapshot(league)
    report = import_roster_csv(league, export_roster_csv(league))
    assert _snapshot(league) == before
    assert report.renamed == 0
    assert report.rerated == 0


def test_every_shipped_player_survives_validation():
    """Guards the enum lists against the data.

    The pools carry synonyms — "Death" and "Death Overs", "Middle-order" and
    "Middle-over Rotator" — so a tidied-up validator would reject the app's own
    export. This fails loudly if the data grows a value the importer rejects.
    """
    league = drafted_league()
    import_roster_csv(league, export_roster_csv(league))  # raises if any row is invalid


# --------------------------------------------------------------------- rename

def test_rename_applies_and_is_reported():
    league = drafted_league()
    text = export_roster_csv(league)
    original = _rows(text)[0]["player_key"]

    report = import_roster_csv(league, _rewrite(text, original, name="Renamed Player"))
    assert report.renamed == 1
    names = {p.name for _, p in _all(league)}
    assert "Renamed Player" in names and original not in names


def test_rename_goes_through_rename_player_so_presets_follow():
    # Setting player.name directly would leave saved presets and match history
    # pointing at a name that no longer exists.
    league = drafted_league()
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    captain = team.captain.name

    text = export_roster_csv(league)
    import_roster_csv(league, _rewrite(text, captain, name="New Captain Name"))

    assert league.user_team().captain.name == "New Captain Name"


def test_two_players_can_swap_names():
    # Applied naively this fails: renaming A->B is rejected while B still exists.
    league = drafted_league()
    text = export_roster_csv(league)
    rows = _rows(text)
    a, b = rows[0]["player_key"], rows[1]["player_key"]

    swapped = _rewrite(_rewrite(text, a, name=b), b, name=a)
    report = import_roster_csv(league, swapped)

    assert report.renamed == 2
    names = {p.name for _, p in _all(league)}
    assert a in names and b in names


def test_rename_colliding_with_an_untouched_player_is_rejected():
    league = drafted_league()
    text = export_roster_csv(league)
    rows = _rows(text)
    a, b = rows[0]["player_key"], rows[1]["player_key"]

    with pytest.raises(RosterImportError) as exc:
        import_roster_csv(league, _rewrite(text, a, name=b))
    assert any("would be used by" in e for e in exc.value.errors)


# ------------------------------------------------------------------ re-rating

def test_ratings_are_applied():
    league = drafted_league()
    text = export_roster_csv(league)
    key = _rows(text)[0]["player_key"]

    report = import_roster_csv(league, _rewrite(text, key, base_ovr=99, batting_ovr=98))
    assert report.rerated == 1
    player = next(p for _, p in _all(league) if p.name == key)
    assert (player.base_ovr, player.batting_ovr) == (99, 98)


@pytest.mark.parametrize(
    "field, value",
    [
        ("base_ovr", 101), ("base_ovr", -1), ("batting_ovr", "high"),
        ("age", 3), ("age", 120), ("natural_slot", 0), ("natural_slot", 12),
        ("role", "Superstar"), ("batting_archetype", "Slogger"),
        ("bowling_phase", "Whenever"), ("batting_hand", "Sideways"),
        ("is_overseas", "maybe"),
    ],
)
def test_invalid_values_are_rejected(field, value):
    league = drafted_league()
    text = export_roster_csv(league)
    key = _rows(text)[0]["player_key"]
    with pytest.raises(RosterImportError):
        import_roster_csv(league, _rewrite(text, key, **{field: value}))


def test_a_rejected_import_changes_nothing():
    """All-or-nothing: a later bad row must not leave earlier rows applied."""
    league = drafted_league()
    text = export_roster_csv(league)
    rows = _rows(text)
    good, bad = rows[0]["player_key"], rows[1]["player_key"]
    before = _snapshot(league)

    edited = _rewrite(_rewrite(text, good, base_ovr=95), bad, age=999)
    with pytest.raises(RosterImportError):
        import_roster_csv(league, edited)
    assert _snapshot(league) == before, "a failed import must not partially apply"


# ------------------------------------------------------------------ structure

def test_unknown_player_key_is_rejected_rather_than_inserted():
    league = drafted_league()
    text = export_roster_csv(league)
    rows = _rows(text)
    rows[0]["player_key"] = "Someone Not In This Career"
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\r\n")
    w.writeheader(); w.writerows(rows)

    with pytest.raises(RosterImportError) as exc:
        import_roster_csv(league, buf.getvalue())
    assert any("no player named" in e for e in exc.value.errors)


def test_duplicate_player_key_is_rejected():
    league = drafted_league()
    rows = _rows(export_roster_csv(league))
    rows.append(dict(rows[0]))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\r\n")
    w.writeheader(); w.writerows(rows)

    with pytest.raises(RosterImportError) as exc:
        import_roster_csv(league, buf.getvalue())
    assert any("more than once" in e for e in exc.value.errors)


def test_partial_file_updates_only_the_rows_present():
    league = drafted_league()
    text = export_roster_csv(league)
    rows = _rows(text)
    keep = rows[0]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\r\n")
    w.writeheader(); w.writerow({**keep, "base_ovr": "77"})

    report = import_roster_csv(league, buf.getvalue())
    assert report.rerated == 1
    player = next(p for _, p in _all(league) if p.name == keep["player_key"])
    assert player.base_ovr == 77


def test_missing_column_is_rejected():
    league = drafted_league()
    with pytest.raises(RosterImportError) as exc:
        import_roster_csv(league, "name,base_ovr\r\nSomeone,50\r\n")
    assert any("Missing column" in e for e in exc.value.errors)


def test_column_order_does_not_matter():
    league = drafted_league()
    rows = _rows(export_roster_csv(league))
    reordered = list(reversed(CSV_COLUMNS))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=reordered, lineterminator="\r\n")
    w.writeheader(); w.writerows(rows)
    import_roster_csv(league, buf.getvalue())  # must not raise


def test_import_flags_the_career_as_edited():
    # Ratings are balance; a modified career must be excludable from any future
    # leaderboard, and that cannot be reconstructed later.
    league = drafted_league()
    assert not getattr(league, "roster_modified", False)
    import_roster_csv(league, export_roster_csv(league))
    assert league.roster_modified is True


def test_team_column_edits_are_ignored_and_reported():
    league = drafted_league()
    text = export_roster_csv(league)
    key = _rows(text)[0]["player_key"]
    report = import_roster_csv(league, _rewrite(text, key, team="Some Other Team"))
    assert report.ignored_team_changes == 1
