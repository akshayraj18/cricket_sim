"""User-supplied player names applied to new careers."""
import csv
import io

import pytest

from cricket_sim_engine.sim.player_names import (
    CSV_COLUMNS,
    NameImportError,
    all_pool_names,
    apply_name_overrides,
    export_names_csv,
    parse_names_csv,
)

from .conftest import drafted_league

pytestmark = pytest.mark.integration


def _rows(text):
    return list(csv.DictReader(io.StringIO(text, newline="")))


def _csv(pairs):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\r\n")
    w.writeheader()
    for key, name in pairs:
        w.writerow({"player_key": key, "name": name})
    return buf.getvalue()


# ---------------------------------------------------------------------- export

def test_export_covers_every_pool_a_career_could_draw_from():
    """Which pool a user meets depends on the career they start, so all count."""
    rows = _rows(export_names_csv())
    keys = {r["player_key"] for r in rows}
    assert keys == set(all_pool_names())
    assert len(keys) > 800, "expected the full cross-pool set, not one pool"


def test_export_defaults_name_to_the_shipped_name():
    for row in _rows(export_names_csv()):
        assert row["name"] == row["player_key"]


def test_export_prefills_saved_overrides():
    # An export must reflect what the user currently has, so it round-trips.
    key = all_pool_names()[0]
    rows = _rows(export_names_csv({key: "My Custom Name"}))
    by_key = {r["player_key"]: r["name"] for r in rows}
    assert by_key[key] == "My Custom Name"


def test_export_round_trips_through_parse():
    assert parse_names_csv(export_names_csv()) == {}, "an unedited export changes nothing"


def test_export_with_overrides_round_trips():
    key = all_pool_names()[0]
    overrides = {key: "Renamed Person"}
    assert parse_names_csv(export_names_csv(overrides)) == overrides


# ----------------------------------------------------------------------- parse

def test_only_changed_rows_are_stored():
    """~900 identity mappings would otherwise be persisted for every user."""
    names = all_pool_names()
    text = _csv([(names[0], "Changed"), (names[1], names[1]), (names[2], names[2])])
    assert parse_names_csv(text) == {names[0]: "Changed"}


def test_unknown_player_key_is_rejected():
    text = _csv([("Not A Real Player", "Whoever")])
    with pytest.raises(NameImportError) as exc:
        parse_names_csv(text)
    assert any("not a player in this game" in e for e in exc.value.errors)


def test_blank_name_is_rejected():
    with pytest.raises(NameImportError):
        parse_names_csv(_csv([(all_pool_names()[0], "")]))


def test_duplicate_player_key_is_rejected():
    key = all_pool_names()[0]
    with pytest.raises(NameImportError) as exc:
        parse_names_csv(_csv([(key, "A"), (key, "B")]))
    assert any("more than once" in e for e in exc.value.errors)


def test_two_players_cannot_share_a_name():
    """A roster's identity IS the name — the draft and scorecards key off it."""
    a, b = all_pool_names()[0], all_pool_names()[1]
    with pytest.raises(NameImportError) as exc:
        parse_names_csv(_csv([(a, "Same Name"), (b, "Same Name")]))
    assert any("would be used by" in e for e in exc.value.errors)


def test_renaming_onto_an_untouched_players_name_is_rejected():
    a, b = all_pool_names()[0], all_pool_names()[1]
    with pytest.raises(NameImportError) as exc:
        parse_names_csv(_csv([(a, b)]))
    assert any("would be used by" in e for e in exc.value.errors)


def test_overlong_name_is_rejected():
    with pytest.raises(NameImportError):
        parse_names_csv(_csv([(all_pool_names()[0], "x" * 200)]))


def test_missing_column_is_rejected():
    with pytest.raises(NameImportError) as exc:
        parse_names_csv("name\r\nSomeone\r\n")
    assert any("Missing column" in e for e in exc.value.errors)


def test_every_problem_is_reported_not_just_the_first():
    text = _csv([("Nobody One", "X"), ("Nobody Two", "Y")])
    with pytest.raises(NameImportError) as exc:
        parse_names_csv(text)
    assert len(exc.value.errors) >= 2


def test_empty_file_is_rejected():
    with pytest.raises(NameImportError):
        parse_names_csv("")


# ----------------------------------------------------------------------- apply

def test_overrides_rename_players_in_a_new_league():
    league = drafted_league()
    target = league.teams[0].roster[0].name
    changed = apply_name_overrides(league, {target: "Brand New Name"})

    assert changed == 1
    names = {p.name for t in league.teams for p in t.roster}
    assert "Brand New Name" in names and target not in names


def test_overrides_also_cover_undrafted_players():
    """A name should look the same whether the player was drafted or not."""
    league = drafted_league()
    pool = league.player_pool or []
    if not pool:
        pytest.skip("no free agents in this league")
    target = pool[0].name
    apply_name_overrides(league, {target: "Free Agent Renamed"})
    assert any(p.name == "Free Agent Renamed" for p in league.player_pool)


def test_no_overrides_is_a_no_op():
    league = drafted_league()
    before = [p.name for t in league.teams for p in t.roster]
    assert apply_name_overrides(league, None) == 0
    assert apply_name_overrides(league, {}) == 0
    assert [p.name for t in league.teams for p in t.roster] == before


def test_overrides_for_absent_players_are_ignored():
    # A user's file covers every pool; any one career only contains some of them.
    league = drafted_league()
    before = [p.name for t in league.teams for p in t.roster]
    assert apply_name_overrides(league, {"Someone Not In This Career": "X"}) == 0
    assert [p.name for t in league.teams for p in t.roster] == before
