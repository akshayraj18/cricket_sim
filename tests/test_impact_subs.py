"""Impact Player substitution: realistic default pairings and end-to-end application during a live match.

Real IPL teams typically bring on an extra specialist bowler when defending
(after batting first) and an extra hitter/finisher when chasing (after
bowling first). `default_impact_subs` should suggest pairings that follow
that pattern, and `LiveMatch.apply_impact_sub` should correctly action
whichever pairing the user has saved, in both directions.
"""
import pytest

from cricket_sim_engine.sim.helpers import is_batting_role, is_bowling_role

from .conftest import (
    apply_smart_presets,
    drafted_league,
    force_toss,
    play_through_innings,
    submit_user_xi_for_innings_role,
)

pytestmark = pytest.mark.integration


def _build_ready_match(seed):
    league = drafted_league(seed=seed)
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    presets = apply_smart_presets(league)
    league.begin_match_day(interactive=True)
    return league, league.live_match, presets


def test_default_impact_subs_returns_both_directions(drafted):
    league = drafted
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    pairings = league.default_impact_subs(team)
    assert set(pairings) == {"bat_to_bowl", "bowl_to_bat"}
    for direction in ("bat_to_bowl", "bowl_to_bat"):
        out_name = pairings[direction]["out"]
        in_name = pairings[direction]["in"]
        assert out_name and in_name, f"{direction} pairing is incomplete: {pairings[direction]}"
        assert out_name != in_name


def test_bat_to_bowl_pairing_brings_in_a_bowling_option(drafted):
    """When defending (having batted first), the suggested swap should bring in a bowling-capable player."""
    league = drafted
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    pairings = league.default_impact_subs(team)
    in_player = next(p for p in team.roster if p.name == pairings["bat_to_bowl"]["in"])
    assert is_bowling_role(in_player), f"expected a bowling option, got {in_player.name} ({in_player.role})"


def test_bowl_to_bat_pairing_brings_in_a_batting_option(drafted):
    """When chasing (having bowled first), the suggested swap should bring in a batting-capable hitter."""
    league = drafted
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    pairings = league.default_impact_subs(team)
    in_player = next(p for p in team.roster if p.name == pairings["bowl_to_bat"]["in"])
    assert is_batting_role(in_player), f"expected a batting option, got {in_player.name} ({in_player.role})"


def test_impact_sub_applies_correctly_when_defending():
    """User bats first; the impact sub should swap in the saved bat_to_bowl pairing and rebuild XI/order/bowling pool/keeper consistently."""
    league, match, presets = _build_ready_match(seed=101)
    team = league.user_team()
    force_toss(match, winner_team=team, decision="bat")
    assert match.inn1_bat == team
    submit_user_xi_for_innings_role(league, match, presets)
    play_through_innings(match)
    assert match.status == "impact"

    xi_before = [p.name for p in match.xis[team.name]]
    sub = team.saved_bat_to_bowl_sub
    assert sub["out"] in xi_before
    bench_before = [p.name for p in team.roster if p.name not in xi_before]
    assert sub["in"] in bench_before

    match.apply_impact_sub(out_name=sub["out"], in_name=sub["in"])

    xi_after = [p.name for p in match.xis[team.name]]
    assert len(xi_after) == 11
    assert len(set(xi_after)) == 11
    assert sub["out"] not in xi_after
    assert sub["in"] in xi_after
    assert sub["out"] not in [p.name for p in match.batting_orders[team.name]]
    assert sub["in"] in [p.name for p in match.batting_orders[team.name]]
    assert all(p.name in xi_after for p in match.bowling_pools[team.name])
    assert match.wicketkeepers[team.name].name in xi_after
    assert any(f"{sub['out']} out, {sub['in']} in" in entry for entry in match.impact_subs)


def test_impact_sub_applies_correctly_when_chasing():
    """User bowls first; the impact sub should swap in the saved bowl_to_bat pairing, then route to setting a chase batting order."""
    league, match, presets = _build_ready_match(seed=202)
    team = league.user_team()
    force_toss(match, winner_team=team, decision="bowl")
    assert match.inn1_bowl == team
    submit_user_xi_for_innings_role(league, match, presets)
    play_through_innings(match)
    assert match.status == "impact"

    xi_before = [p.name for p in match.xis[team.name]]
    sub = team.saved_bowl_to_bat_sub
    assert sub["out"] in xi_before
    bench_before = [p.name for p in team.roster if p.name not in xi_before]
    assert sub["in"] in bench_before

    match.apply_impact_sub(out_name=sub["out"], in_name=sub["in"])

    xi_after = [p.name for p in match.xis[team.name]]
    assert len(xi_after) == 11
    assert len(set(xi_after)) == 11
    assert sub["out"] not in xi_after
    assert sub["in"] in xi_after
    # User is now batting (chasing) -> moves on to set a batting order for the second innings.
    assert match.status == "batting_order"
    assert sub["in"] in [p.name for p in match.batting_orders[team.name]]
    assert sub["out"] not in [p.name for p in match.batting_orders[team.name]]


def test_impact_sub_rejects_player_not_in_xi_or_bench():
    league, match, presets = _build_ready_match(seed=303)
    team = league.user_team()
    force_toss(match, winner_team=team, decision="bat")
    submit_user_xi_for_innings_role(league, match, presets)
    play_through_innings(match)
    assert match.status == "impact"

    xi_names = [p.name for p in match.xis[team.name]]
    bench_names = [p.name for p in team.roster if p.name not in xi_names]
    import pytest
    with pytest.raises(ValueError):
        match.apply_impact_sub(out_name=bench_names[0], in_name=bench_names[1])


def test_declining_impact_sub_still_advances_match():
    """A user can skip their Impact Player sub entirely — the match should still proceed to the second innings/result."""
    league, match, presets = _build_ready_match(seed=404)
    team = league.user_team()
    force_toss(match, winner_team=team, decision="bat")
    submit_user_xi_for_innings_role(league, match, presets)
    play_through_innings(match)
    assert match.status == "impact"
    xi_before = [p.name for p in match.xis[team.name]]

    match.apply_impact_sub()  # no names -> declines the sub

    assert [p.name for p in match.xis[team.name]] == xi_before
    assert match.status in ("over", "batting_order", "complete")
