"""Leadership lock: captain, vice-captain, and designated wicketkeeper must
always be in the saved Starting XI, and can never be the player subbed out
via the Impact Sub.
"""
import pytest

from cricket_sim_engine.sim.helpers import is_wicketkeeper_option

from .conftest import (
    apply_smart_presets,
    drafted_league,
    force_toss,
    play_through_innings,
    resolve,
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


def test_set_user_presets_requires_a_wicketkeeper_in_starting_xi(drafted):
    league = drafted
    team = league.user_team()
    starting_xi_names = league.smart_starting_xi(team)
    xi = resolve(team, starting_xi_names)
    keeper = next(p for p in xi if is_wicketkeeper_option(p))
    bench_non_keeper = next(
        p for p in team.roster if p.name not in starting_xi_names and not is_wicketkeeper_option(p)
    )
    no_keeper_xi = [bench_non_keeper.name if name == keeper.name else name for name in starting_xi_names]

    with pytest.raises(ValueError):
        league.set_user_presets([], [], starting_xi=no_keeper_xi)


def test_set_user_presets_auto_reassigns_leadership_when_outside_new_xi(drafted):
    """If the saved Starting XI changes such that the current captain/vice-captain/keeper
    fall outside it, leadership is auto-reassigned by current_ovr rather than rejected.
    """
    league = drafted
    team = league.user_team()
    starting_xi_names = league.smart_starting_xi(team)
    league.set_user_presets([], [], starting_xi=starting_xi_names)
    league.set_leadership(team.captain.name, team.vice_captain.name, wicketkeeper_name=team.saved_wicketkeeper_name)

    old_captain = team.captain
    bench = [p for p in team.roster if p.name not in starting_xi_names]
    # Replace the captain with a bench player of the same overseas status and a
    # non-keeper role, so the new XI still respects the 4-overseas cap and keeps
    # its lone wicketkeeper — isolating the leadership auto-reassignment behaviour.
    replacement = next(
        p for p in bench
        if not is_wicketkeeper_option(p) and p.is_overseas == old_captain.is_overseas
    )
    new_xi_names = [replacement.name if name == old_captain.name else name for name in starting_xi_names]

    league.set_user_presets([], [], starting_xi=new_xi_names)

    assert team.captain.name in new_xi_names
    assert team.vice_captain.name in new_xi_names
    assert team.saved_wicketkeeper_name in new_xi_names
    assert is_wicketkeeper_option(next(p for p in team.roster if p.name == team.saved_wicketkeeper_name))

    new_xi = resolve(team, new_xi_names)
    ranked = sorted(new_xi, key=lambda p: p.current_ovr, reverse=True)
    assert team.captain.name == ranked[0].name
    assert team.vice_captain.name == ranked[1].name


def test_set_leadership_rejects_player_not_in_starting_xi(drafted):
    league = drafted
    team = league.user_team()
    starting_xi_names = league.smart_starting_xi(team)
    league.set_user_presets([], [], starting_xi=starting_xi_names)

    bench_player = next(p for p in team.roster if p.name not in starting_xi_names)
    xi_player = next(p for p in team.roster if p.name in starting_xi_names and p != bench_player)

    with pytest.raises(ValueError):
        league.set_leadership(bench_player.name, xi_player.name)

    with pytest.raises(ValueError):
        league.set_leadership(xi_player.name, bench_player.name)


def test_apply_impact_sub_rejects_subbing_out_captain_vice_or_keeper():
    league, match, presets = _build_ready_match(seed=101)
    team = league.user_team()
    force_toss(match, winner_team=team, decision="bat")
    submit_user_xi_for_innings_role(league, match, presets)
    play_through_innings(match)
    assert match.status == "impact"

    xi = match.xis[team.name]
    bench_names = [p.name for p in team.roster if p not in xi]
    assert bench_names

    # A leader who is currently in the XI cannot be the player subbed out.
    leader_names = {team.captain.name, team.vice_captain.name, team.saved_wicketkeeper_name}
    leader_in_xi = next((p.name for p in xi if p.name in leader_names), None)
    assert leader_in_xi, "expected at least one leader in the playing XI"
    with pytest.raises(ValueError):
        match.apply_impact_sub(out_name=leader_in_xi, in_name=bench_names[0])


def test_resolve_match_xi_never_swaps_out_leadership(drafted):
    league = drafted
    team = league.user_team()
    starting_xi_names = league.smart_starting_xi(team)
    impact_sub_name = league.smart_impact_sub(team, starting_xi_names)
    league.set_user_presets([], [], starting_xi=starting_xi_names, impact_sub_name=impact_sub_name)
    league.set_leadership(team.captain.name, team.vice_captain.name, wicketkeeper_name=team.saved_wicketkeeper_name)

    leader_names = {team.captain.name, team.vice_captain.name, team.saved_wicketkeeper_name}

    _innings1_xi, swap_out, swap_in = league.resolve_match_xi(team, batting_first=True)
    assert swap_out not in leader_names

    innings1_xi, swap_out, swap_in = league.resolve_match_xi(team, batting_first=False)
    # Bowling first: the returned swap_out is the impact sub (who leaves at the
    # break) and swap_in is the original Starting XI player who sits out innings 1
    # and returns at the break. That sat-out player must never be a leader, and
    # every leader must remain in the innings-1 XI.
    assert swap_in not in leader_names
    for name in leader_names:
        if name:
            assert name in innings1_xi
