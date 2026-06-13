"""Impact Player substitution: the "11+1" default pairing and end-to-end application during a live match.

Under the "11+1" model, `resolve_match_xi` derives a single swap pairing from
the user's Starting XI + Impact Sub: batting first, the Impact Sub (a
bowling-heavy "12th player") comes on for a Starting XI player at the break;
bowling first, the Impact Sub already starts in place of that player and the
original returns at the break. `LiveMatch.apply_impact_sub` should correctly
action whichever pairing is in effect, in both directions.
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


def test_resolve_match_xi_batting_first_brings_in_a_bowling_option_at_the_break(drafted):
    """When defending (batting first), the swap-in at the break should be a bowling-capable Impact Sub."""
    league = drafted
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    apply_smart_presets(league)
    _innings1_xi, swap_out, swap_in = league.resolve_match_xi(team, batting_first=True)
    assert swap_out and swap_in and swap_out != swap_in
    in_player = next(p for p in team.roster if p.name == swap_in)
    assert is_bowling_role(in_player), f"expected a bowling option, got {in_player.name} ({in_player.role})"


def test_resolve_match_xi_bowling_first_returns_a_batting_option_at_the_break(drafted):
    """When chasing (bowling first), the player who returns at the break should be a batting-capable starter."""
    league = drafted
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    apply_smart_presets(league)
    _innings1_xi, swap_out, swap_in = league.resolve_match_xi(team, batting_first=False)
    assert swap_out and swap_in and swap_out != swap_in
    in_player = next(p for p in team.roster if p.name == swap_in)
    assert is_batting_role(in_player), f"expected a batting option, got {in_player.name} ({in_player.role})"


def test_impact_sub_applies_correctly_when_defending():
    """User bats first; the impact sub should swap in the pending Impact Sub pairing and rebuild XI/order/bowling pool/keeper consistently."""
    league, match, presets = _build_ready_match(seed=101)
    team = league.user_team()
    force_toss(match, winner_team=team, decision="bat")
    assert match.inn1_bat == team
    submit_user_xi_for_innings_role(league, match, presets)
    play_through_innings(match)
    assert match.status == "impact"

    xi_before = [p.name for p in match.xis[team.name]]
    swap_out, swap_in = match.pending_swaps[team.name]
    sub = {"out": swap_out, "in": swap_in}
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
    """User bowls first; the impact sub should swap in the pending Impact Sub pairing, then route to setting a chase batting order."""
    league, match, presets = _build_ready_match(seed=202)
    team = league.user_team()
    force_toss(match, winner_team=team, decision="bowl")
    assert match.inn1_bowl == team
    submit_user_xi_for_innings_role(league, match, presets)
    play_through_innings(match)
    assert match.status == "impact"

    xi_before = [p.name for p in match.xis[team.name]]
    swap_out, swap_in = match.pending_swaps[team.name]
    sub = {"out": swap_out, "in": swap_in}
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
    order_after = [p.name for p in match.batting_orders[team.name]]
    assert sub["in"] in order_after
    assert sub["out"] not in order_after

    # The returning batter should reclaim roughly their original slot in the
    # squad's Starting XI batting order, not get appended to the tail.
    starting_order = league.default_batting_order(team)
    natural_idx = starting_order.index(sub["in"])
    assert abs(order_after.index(sub["in"]) - natural_idx) <= 1
    if natural_idx != 10:
        assert order_after.index(sub["in"]) != 10

    # The chase-stage payload's `lineup_xi` (what the mobile editor seeds from)
    # must reflect the post-sub batting order — not re-derive resolve_match_xi,
    # which would put the returning batter back at the tail.
    payload_xi = match.payload()["lineup_xi"]
    assert payload_xi == order_after


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
