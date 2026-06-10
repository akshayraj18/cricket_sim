"""Draft flow: starting a league, drafting a squad, and validating roster composition."""
import pytest

from sim.helpers import is_batting_role, is_bowling_role, is_wicketkeeper_option
from sim.league_state import LeagueState

pytestmark = pytest.mark.integration


def test_new_league_sets_up_blank_draft(league):
    assert league.phase == "draft"
    assert league.user_team_name == "Mumbai Indians"
    assert len(league.teams) == 10
    assert all(len(t.roster) == 0 for t in league.teams)


def test_new_league_rejects_unknown_franchise():
    state = LeagueState()
    with pytest.raises(ValueError):
        state.new_league("Made Up Franchise XI", "medium")


def test_autodraft_fills_every_squad_to_21(drafted):
    for team in drafted.teams:
        assert len(team.roster) == 21, f"{team.name} has {len(team.roster)} players"
    assert drafted.phase == "season"


def test_drafted_squad_has_balanced_roles(drafted):
    team = drafted.user_team()
    keepers = [p for p in team.roster if is_wicketkeeper_option(p)]
    batters = [p for p in team.roster if is_batting_role(p)]
    bowlers = [p for p in team.roster if is_bowling_role(p)]
    assert keepers, "squad should include at least one wicketkeeper option"
    assert len(batters) >= 6
    assert len(bowlers) >= 5


def test_every_drafted_player_has_a_preferred_position(drafted):
    for team in drafted.teams:
        for p in team.roster:
            assert 1 <= p.preferred_position <= 11, f"{p.name} has bad preferred_position {p.preferred_position}"


def test_no_player_drafted_twice(drafted):
    seen = set()
    for team in drafted.teams:
        for p in team.roster:
            assert p.name not in seen, f"{p.name} drafted onto multiple squads"
            seen.add(p.name)


def test_overseas_limit_not_exceeded_in_any_squad(drafted):
    for team in drafted.teams:
        overseas = sum(1 for p in team.roster if p.is_overseas)
        assert overseas <= 8, f"{team.name} drafted an unrealistic {overseas} overseas players"


def test_new_league_with_rosters_skips_draft_and_assigns_real_squads():
    state = LeagueState()
    state.new_league_with_rosters("Mumbai Indians", "medium")
    assert state.phase == "season"
    assert state.draft_pool_type == "rosters2026"
    user = state.user_team()
    assert "Jasprit Bumrah" in [p.name for p in user.roster]
    assert all(len(t.roster) >= 21 for t in state.teams)
    assert all(t.captain and t.vice_captain for t in state.teams)


def test_new_league_with_rosters_has_no_duplicate_or_missing_players():
    state = LeagueState()
    state.new_league_with_rosters("Mumbai Indians", "medium")
    all_names = [p.name for t in state.teams for p in t.roster] + [p.name for p in state.player_pool]
    assert len(all_names) == len(set(all_names)), "every player should appear at most once across rosters and the pool"
    assert len(all_names) == len(state.player_pool) + sum(len(t.roster) for t in state.teams)


def test_new_league_with_rosters_rejects_unknown_franchise():
    state = LeagueState()
    with pytest.raises(ValueError):
        state.new_league_with_rosters("Made Up Franchise XI", "medium")
