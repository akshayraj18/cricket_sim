"""Tests for `players_data.py`: loading player pools from CSV and building 2026 rosters.

These exercise the real `players.csv`/`players_alltime.csv` shipped with the
repo (both required to run the app), checking the loaded `Player` objects are
well-formed and that the 2026-roster split partitions the current-era pool
correctly.
"""
import pytest

from cricket_sim_engine.models import Player
from cricket_sim_engine.players_data import (
    IPL_2026_ROSTERS,
    IPL_TEAMS_LIST,
    get_2026_rosters_and_pool,
    get_alltime_player_pool,
    get_initial_player_pool,
)

pytestmark = pytest.mark.unit


# --- get_initial_player_pool --------------------------------------------------------

def test_initial_pool_has_at_least_180_players():
    pool = get_initial_player_pool()
    assert len(pool) >= 180


def test_initial_pool_entries_are_players_with_valid_ratings():
    pool = get_initial_player_pool()
    for p in pool:
        assert isinstance(p, Player)
        assert 1 <= p.base_ovr <= 100
        assert 1 <= p.batting_ovr <= 100
        assert 1 <= p.bowling_ovr <= 100
        assert p.age > 0
        assert 1 <= p.preferred_position <= 11


def test_initial_pool_contains_players_from_csv():
    pool = get_initial_player_pool()
    names = {p.name for p in pool}
    # Names are the fictional (IP-safe) names shipped in players.csv.
    assert "Jesprit Bomrah" in names
    assert "Vyrat Kuhli" in names


def test_initial_pool_has_no_duplicate_names():
    pool = get_initial_player_pool()
    names = [p.name for p in pool]
    assert len(names) == len(set(names))


def test_initial_pool_padding_uses_domestic_prospect_names_when_short():
    pool = get_initial_player_pool()
    prospects = [p for p in pool if p.name.startswith("Domestic_Prospect_")]
    # players.csv has > 180 rows, so no padding should be required currently —
    # but if it ever drops below 180, padding kicks in with valid players.
    for p in prospects:
        assert 18 <= p.age <= 25
        assert p.role in ("Batsman", "Bowler (Fast)", "Bowler (Spin)", "All-Rounder", "Wicketkeeper")


def test_natural_slot_column_overrides_derived_position():
    pool = get_initial_player_pool()
    bumrah = next(p for p in pool if p.name == "Jesprit Bomrah")
    assert bumrah.preferred_position == 11  # natural_slot column in players.csv


# --- get_alltime_player_pool ----------------------------------------------------------

def test_alltime_pool_has_many_players():
    pool = get_alltime_player_pool()
    assert len(pool) >= 180


def test_alltime_pool_entries_are_valid_players():
    pool = get_alltime_player_pool()
    for p in pool:
        assert isinstance(p, Player)
        assert 1 <= p.base_ovr <= 100
        assert 1 <= p.preferred_position <= 11


def test_alltime_pool_contains_legends():
    pool = get_alltime_player_pool()
    names = {p.name for p in pool}
    # Fictional (IP-safe) names from players_alltime.csv.
    assert "AB de Vylliers" in names
    assert "Chrys Geyle" in names


def test_alltime_pool_has_no_duplicate_names():
    pool = get_alltime_player_pool()
    names = [p.name for p in pool]
    assert len(names) == len(set(names))


# --- get_2026_rosters_and_pool ------------------------------------------------------

def test_2026_rosters_cover_all_ipl_teams():
    rosters, _ = get_2026_rosters_and_pool()
    assert set(rosters.keys()) == set(IPL_TEAMS_LIST)


def test_2026_rosters_match_configured_squads():
    rosters, _ = get_2026_rosters_and_pool()
    for team_name, expected_names in IPL_2026_ROSTERS.items():
        actual_names = {p.name for p in rosters[team_name]}
        # Every roster player resolved from players.csv should be present;
        # any name in IPL_2026_ROSTERS not found in players.csv is silently skipped.
        assert actual_names <= set(expected_names)
        assert actual_names, f"{team_name} roster resolved to zero players"


def test_2026_rosters_and_leftover_pool_partition_initial_pool():
    rosters, leftover_pool = get_2026_rosters_and_pool()
    initial_pool = get_initial_player_pool()
    initial_names = {p.name for p in initial_pool}

    roster_names = set()
    for squad in rosters.values():
        roster_names.update(p.name for p in squad)

    leftover_names = {p.name for p in leftover_pool}

    # No overlap between rostered and leftover players.
    assert roster_names.isdisjoint(leftover_names)
    # Together they account for every player in players.csv.
    assert roster_names | leftover_names == initial_names


def test_2026_rosters_have_no_player_assigned_to_two_teams():
    rosters, _ = get_2026_rosters_and_pool()
    seen = set()
    for squad in rosters.values():
        for p in squad:
            assert p.name not in seen, f"{p.name} assigned to multiple 2026 rosters"
            seen.add(p.name)


@pytest.mark.parametrize("team_name", IPL_TEAMS_LIST)
def test_each_2026_roster_has_at_least_squad_minimum(team_name):
    rosters, _ = get_2026_rosters_and_pool()
    # Configured rosters list ~24-25 names each; at least most should resolve.
    assert len(rosters[team_name]) >= 18
