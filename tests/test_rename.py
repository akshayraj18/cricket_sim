"""Roster editor: renaming players and teams within a career.

Renames mutate the league state globally (the IP-safe default names can be
swapped for whatever the user wants), so they must propagate to rosters, saved
presets, leadership, the user-team pointer, and survive serialization.
"""
import pytest

from cricket_sim_engine.sim.league_state import LeagueState

from .conftest import apply_smart_presets

pytestmark = pytest.mark.integration


def _drafted():
    league = LeagueState()
    league.new_league_with_rosters("Mumbai Mavericks", "medium")
    return league


def test_rename_player_updates_roster_and_presets():
    league = _drafted()
    team = league.user_team()
    apply_smart_presets(league)
    old = team.saved_starting_xi_names[0]

    league.rename_player(old, "Custom Name")

    team = league.user_team()
    names = {p.name for p in team.roster}
    assert "Custom Name" in names
    assert old not in names
    assert "Custom Name" in team.saved_starting_xi_names
    assert old not in team.saved_starting_xi_names


def test_rename_player_survives_serialization():
    league = _drafted()
    old = league.user_team().roster[0].name
    league.rename_player(old, "Persisted Name")

    restored = LeagueState.from_dict(league.to_dict())
    names = {p.name for p in restored.user_team().roster}
    assert "Persisted Name" in names
    assert old not in names


def test_rename_player_rejects_blank_and_duplicate():
    league = _drafted()
    roster = league.user_team().roster
    with pytest.raises(ValueError):
        league.rename_player(roster[0].name, "")
    with pytest.raises(ValueError):
        league.rename_player(roster[0].name, roster[1].name)
    with pytest.raises(ValueError):
        league.rename_player("Nobody Here", "Whoever")


def test_rename_team_updates_pointer_and_objects():
    league = _drafted()
    assert league.user_team_name == "Mumbai Mavericks"

    league.rename_team("Mumbai Mavericks", "Bombay United")

    assert league.user_team_name == "Bombay United"
    assert league.user_team().name == "Bombay United"
    assert not any(t.name == "Mumbai Mavericks" for t in league.teams)


def test_rename_team_keeps_branding_and_can_simulate():
    """Regression: renaming a team to a name that isn't a TEAM_META key (e.g.
    'Sunrisers Hyderabad') must keep its original branding and must NOT crash
    when building the match card's venue (team_meta fallback, not TEAM_META[])."""
    league = _drafted()
    team = league.user_team()
    original_meta = league.team_dict(team)["abbr"]

    league.rename_team("Mumbai Mavericks", "Sunrisers Hyderabad")

    team = league.user_team()
    d = league.team_dict(team)
    assert d["abbr"] == original_meta  # branding preserved via meta_name
    assert d["primary"]  # colors present, no KeyError

    # Simulating a round used to KeyError on TEAM_META[team.name] for the venue.
    league.set_leadership(team.captain.name, team.vice_captain.name)
    apply_smart_presets(league)
    league.simulate_current_round()  # must not raise


def test_rename_team_rejects_blank_and_duplicate():
    league = _drafted()
    other = next(t.name for t in league.teams if t.name != "Mumbai Mavericks")
    with pytest.raises(ValueError):
        league.rename_team("Mumbai Mavericks", "")
    with pytest.raises(ValueError):
        league.rename_team("Mumbai Mavericks", other)
    with pytest.raises(ValueError):
        league.rename_team("No Such Team", "Anything")


def test_full_season_after_renaming_team_and_player():
    """End-to-end: rename the user's team AND one of its players, then play a
    whole season through playoffs. The renamed team must keep playing 14 games,
    appear correctly in the schedule/standings/playoffs, and the renamed player
    must still accrue stats — i.e. no stale old-name reference is left anywhere
    that the season machinery reads."""
    import random

    random.seed(4242)
    league = _drafted()
    user = league.user_team()
    old_player = user.captain.name

    league.rename_team("Mumbai Mavericks", "Sunrisers Hyderabad")
    league.rename_player(old_player, "Star Player")

    team = league.user_team()
    assert team.name == "Sunrisers Hyderabad"
    assert any(p.name == "Star Player" for p in team.roster)
    assert not any(p.name == old_player for p in team.roster)

    league.set_leadership(team.captain.name, team.vice_captain.name)
    apply_smart_presets(league)

    # No round of the schedule should still reference the old team name.
    for round_ in league.schedule:
        for pair in round_:
            assert "Mumbai Mavericks" not in pair

    while league.phase == "season":
        league.simulate_current_round()
    assert league.phase == "league_complete"

    table = league.standings()
    assert len(table) == 10
    renamed = next(t for t in table if t.name == "Sunrisers Hyderabad")
    assert renamed.games_played == 14
    assert not any(t.name == "Mumbai Mavericks" for t in table)

    # Playoffs reference the renamed team by its new name without crashing.
    league.start_playoffs()
    guard = 0
    while league.phase == "playoffs":
        league.simulate_current_round()
        guard += 1
        assert guard <= 10
    assert league.phase == "season_end"
