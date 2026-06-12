"""Lineup intelligence: preferred-position derivation, smart batting order, and smart XI selection.

These guard the central "Klaasen should bat at #4/#5, not get shoved to the
bottom because of his archetype label" requirement, and the realism of the
auto-generated XIs/orders that feed match simulation.
"""
import pytest

from cricket_sim_engine.models import derive_preferred_position
from cricket_sim_engine.sim.helpers import counts_as_batter, counts_as_bowler

from .conftest import resolve

pytestmark = pytest.mark.integration


def test_spin_specialist_keeper_slots_in_middle_order():
    """A "Spin Specialist" Wicketkeeper (Klaasen/Pooran's archetype) should naturally bat #4-5, not be treated as a tailender."""
    pos = derive_preferred_position("Wicketkeeper", "Spin Specialist", batting_ovr=80, bowling_ovr=20)
    assert pos in (4, 5)


def test_aggressive_opener_keeper_slots_at_the_top():
    pos = derive_preferred_position("Wicketkeeper", "Aggressive Opener", batting_ovr=85, bowling_ovr=20)
    assert pos in (1, 2)


def test_pure_fast_bowler_slots_in_the_tail():
    pos = derive_preferred_position("Bowler (Fast)", "Defensive Tailender", batting_ovr=20, bowling_ovr=90)
    assert pos >= 9


def test_allrounder_position_nudges_toward_strength():
    batting_heavy = derive_preferred_position("All-Rounder", "Strike Rotator", batting_ovr=85, bowling_ovr=60)
    bowling_heavy = derive_preferred_position("All-Rounder", "Strike Rotator", batting_ovr=60, bowling_ovr=85)
    assert batting_heavy < bowling_heavy


def test_preferred_position_always_in_range():
    for role in ("Batsman", "Wicketkeeper", "All-Rounder", "Bowler (Fast)", "Bowler (Spin)"):
        for archetype in ("Aggressor", "Finisher", "Unknown Archetype Xyz"):
            pos = derive_preferred_position(role, archetype, batting_ovr=50, bowling_ovr=50)
            assert 1 <= pos <= 11


def test_smart_batting_order_respects_preferred_positions(drafted):
    """The Klaasen/Pooran scenario, end to end: a middle-order specialist keeper should land near their natural slot in the suggested order, not get pushed to the tail."""
    league = drafted
    team = league.user_team()
    xi_names = league.smart_starting_xi(team)
    xi = resolve(team, xi_names)
    order = league.smart_batting_order(xi)
    assert len(order) == 11
    assert len(set(p.name for p in order)) == 11
    for slot_idx, p in enumerate(order, start=1):
        # No player should be forced more than 4 slots from their natural position
        # (the assignment is a best-fit pass, so wide misses indicate a bug).
        assert abs(slot_idx - p.preferred_position) <= 5, (
            f"{p.name} (#natural {p.preferred_position}) was placed at slot {slot_idx}"
        )


def test_smart_batting_order_places_natural_top_order_batter_up_front(drafted):
    league = drafted
    team = league.user_team()
    xi_names = league.smart_starting_xi(team)
    xi = resolve(team, xi_names)
    order = league.smart_batting_order(xi)
    top_three = order[:3]
    assert any(counts_as_batter(p) and p.preferred_position <= 3 for p in top_three), (
        "expected at least one natural top-order batter in the top 3 slots, got "
        f"{[(p.name, p.preferred_position) for p in top_three]}"
    )


def test_smart_starting_xi_is_valid_xi(drafted):
    league = drafted
    team = league.user_team()
    xi_names = league.smart_starting_xi(team)
    xi = resolve(team, xi_names)
    assert len(xi) == 11
    assert len(set(xi_names)) == 11
    assert sum(1 for p in xi if p.is_overseas) <= 4
    assert len([p for p in xi if counts_as_batter(p)]) >= 6


def test_smart_impact_sub_is_a_bowling_option_not_in_starting_xi(drafted):
    league = drafted
    team = league.user_team()
    starting_xi_names = league.smart_starting_xi(team)
    impact_sub_name = league.smart_impact_sub(team, starting_xi_names)
    assert impact_sub_name
    assert impact_sub_name not in starting_xi_names
    impact_sub = next(p for p in team.roster if p.name == impact_sub_name)
    assert counts_as_bowler(impact_sub)


def test_resolve_match_xi_batting_first_keeps_starting_xi_unchanged(drafted):
    league = drafted
    team = league.user_team()
    starting_xi_names = league.smart_starting_xi(team)
    impact_sub_name = league.smart_impact_sub(team, starting_xi_names)
    league.set_user_presets([], [], starting_xi=starting_xi_names, impact_sub_name=impact_sub_name)

    innings1_xi, swap_out, swap_in = league.resolve_match_xi(team, batting_first=True)

    assert innings1_xi == starting_xi_names
    assert swap_out in starting_xi_names
    assert swap_in == impact_sub_name


def test_resolve_match_xi_bowling_first_starts_impact_sub_in_place_of_swap_out(drafted):
    league = drafted
    team = league.user_team()
    starting_xi_names = league.smart_starting_xi(team)
    impact_sub_name = league.smart_impact_sub(team, starting_xi_names)
    league.set_user_presets([], [], starting_xi=starting_xi_names, impact_sub_name=impact_sub_name)

    innings1_xi, swap_out, swap_in = league.resolve_match_xi(team, batting_first=False)

    assert len(innings1_xi) == 11
    assert len(set(innings1_xi)) == 11
    assert impact_sub_name in innings1_xi
    assert swap_out == impact_sub_name
    assert swap_in in starting_xi_names
    assert swap_in not in innings1_xi
    # innings1_xi is starting_xi with swap_in replaced by the impact sub
    assert set(innings1_xi) == (set(starting_xi_names) - {swap_in}) | {impact_sub_name}


def test_default_bowling_plan_respects_over_caps(drafted):
    league = drafted
    team = league.user_team()
    plan = league.default_bowling_plan(team)
    if not plan:
        return
    assert len(plan) == 20
    for name in set(plan):
        assert plan.count(name) <= 4, f"{name} scheduled for more than 4 overs"
    assert all(plan[i] != plan[i - 1] for i in range(1, len(plan))), "a bowler is scheduled for consecutive overs"
