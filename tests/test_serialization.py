"""Round-trip JSON serialization tests for Player/Team/LeagueState (DB persistence)."""
import json

import pytest

from cricket_sim_engine.models import Player, Team
from cricket_sim_engine.sim.league_state import LeagueState

from .conftest import USER_TEAM, apply_smart_presets, drafted_league, fresh_league


pytestmark = pytest.mark.unit


def test_player_round_trip_preserves_fields():
    original = Player(
        name="Test Player", role="All-Rounder", base_ovr=80, batting_ovr=78, bowling_ovr=80,
        is_overseas=True, age=27, batting_hand="Left", bowling_hand="Right",
        batting_archetype="Finisher", bowling_phase="Death Overs", bowling_type="Right-arm Fast",
        strengths="Death hitting", weaknesses="Spin vulnerability",
    )
    original.form = 7.5
    original.intent = "Aggressive"
    original.team_name = "Mumbai Mavericks"
    original.stats["runs"] = 123
    original.stats["wickets"] = 4
    original.season_start_ovr = 75

    restored = Player.from_dict(original.to_dict())

    assert restored.name == original.name
    assert restored.role == original.role
    assert restored.base_ovr == original.base_ovr
    assert restored.batting_ovr == original.batting_ovr
    assert restored.bowling_ovr == original.bowling_ovr
    assert restored.is_overseas == original.is_overseas
    assert restored.age == original.age
    assert restored.batting_hand == original.batting_hand
    assert restored.bowling_hand == original.bowling_hand
    assert restored.batting_archetype == original.batting_archetype
    assert restored.bowling_phase == original.bowling_phase
    assert restored.bowling_type == original.bowling_type
    assert restored.strengths == original.strengths
    assert restored.weaknesses == original.weaknesses
    assert restored.preferred_position == original.preferred_position
    assert restored.form == original.form
    assert restored.intent == original.intent
    assert restored.team_name == original.team_name
    assert restored.stats == original.stats
    assert restored.season_start_ovr == 75


def test_player_to_dict_is_json_safe():
    p = Player("Json Player", "Batsman", 70, 70, 20, False, 24)
    json.dumps(p.to_dict())


def test_team_round_trip_preserves_roster_and_leadership():
    team = Team("Mumbai Mavericks")
    p1 = Player("Captain Player", "Batsman", 85, 85, 20, False, 30)
    p2 = Player("Vice Captain Player", "Bowler (Fast)", 80, 20, 80, True, 28)
    p3 = Player("Bench Player", "All-Rounder", 70, 65, 65, False, 22)
    team.roster = [p1, p2, p3]
    team.captain = p1
    team.vice_captain = p2
    team.points = 12
    team.wins = 6
    team.losses = 2
    team.saved_wicketkeeper_name = "Bench Player"
    team.saved_batting_order_names = [p.name for p in (p1, p2, p3)]
    team.saved_starting_xi_names = [p.name for p in (p1, p2, p3)]
    team.saved_impact_sub_name = p3.name

    restored = Team.from_dict(team.to_dict())

    assert restored.name == team.name
    assert [p.name for p in restored.roster] == [p1.name, p2.name, p3.name]
    assert restored.captain.name == p1.name
    assert restored.vice_captain.name == p2.name
    # captain/vice_captain must be the *same objects* as in the restored roster
    assert restored.captain is restored.roster[0]
    assert restored.vice_captain is restored.roster[1]
    assert restored.points == 12
    assert restored.wins == 6
    assert restored.losses == 2
    assert restored.saved_wicketkeeper_name == "Bench Player"
    assert restored.saved_batting_order_names == team.saved_batting_order_names
    assert restored.saved_starting_xi_names == team.saved_starting_xi_names
    assert restored.saved_impact_sub_name == team.saved_impact_sub_name


def test_team_round_trip_with_no_leadership():
    team = Team("Chennai Cholas")
    restored = Team.from_dict(team.to_dict())
    assert restored.captain is None
    assert restored.vice_captain is None
    assert restored.roster == []


def test_league_state_round_trip_during_draft():
    league = fresh_league()
    league.start_draft()

    restored = LeagueState.from_dict(league.to_dict())

    assert restored.phase == league.phase
    assert restored.season_year == league.season_year
    assert restored.user_team_name == league.user_team_name
    assert restored.difficulty == league.difficulty
    assert restored.draft_pool_type == league.draft_pool_type
    assert [t.name for t in restored.teams] == [t.name for t in league.teams]
    assert [p.name for p in restored.player_pool] == [p.name for p in league.player_pool]
    assert restored.draft_round == league.draft_round
    assert restored.draft_index == league.draft_index
    assert restored.pick_num == league.pick_num
    assert restored.draft_history == league.draft_history
    assert restored.live_match is None

    # draft_order resolves to the *restored* team objects, not the originals.
    assert [t.name for t in restored.draft_order] == [t.name for t in league.draft_order]
    for team in restored.draft_order:
        assert team in restored.teams


def test_league_state_round_trip_mid_season():
    league = drafted_league()
    apply_smart_presets(league)
    # Simulate a round so points/standings/history are non-trivial.
    league.simulate_current_round()

    restored = LeagueState.from_dict(league.to_dict())

    assert restored.phase == league.phase
    assert restored.round_num == league.round_num
    assert restored.schedule == league.schedule
    assert restored.match_log == league.match_log
    assert restored.fixture_results == league.fixture_results

    user_team = restored.find_team(USER_TEAM)
    original_user_team = league.find_team(USER_TEAM)
    assert user_team.points == original_user_team.points
    assert user_team.wins == original_user_team.wins
    assert user_team.losses == original_user_team.losses
    assert user_team.saved_batting_order_names == original_user_team.saved_batting_order_names
    assert user_team.saved_bowling_over_names == original_user_team.saved_bowling_over_names

    # Roster stats survived the round trip.
    original_player = next(p for p in original_user_team.roster if p.stats["balls_faced"] > 0 or p.stats["balls_bowled"] > 0)
    restored_player = next(p for p in user_team.roster if p.name == original_player.name)
    assert restored_player.stats == original_player.stats


def test_league_state_to_dict_excludes_live_match_and_is_json_safe():
    league = drafted_league()
    league.begin_match_day(interactive=True)
    assert league.live_match is not None

    blob = league.to_dict()
    assert "live_match" not in blob
    json.dumps(blob)  # must be fully JSON-serialisable

    restored = LeagueState.from_dict(blob)
    assert restored.live_match is None


def test_league_state_round_trip_preserves_standings_and_history():
    league = drafted_league()
    apply_smart_presets(league)
    for _ in range(14):
        league.simulate_current_round()
    assert league.phase == "league_complete"
    assert league.last_standings

    restored = LeagueState.from_dict(league.to_dict())

    assert [t.name for t in restored.last_standings] == [t.name for t in league.last_standings]
    assert restored.pending_playoff_top_four == league.pending_playoff_top_four
    for team in restored.last_standings:
        assert team in restored.teams
