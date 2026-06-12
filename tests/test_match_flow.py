"""End-to-end live-match flow: toss, lineup submission, simulation to completion, and result recording."""
import pytest

from .conftest import (
    apply_smart_presets,
    drafted_league,
    force_toss,
    play_through_innings,
    submit_user_xi_for_innings_role,
)

pytestmark = pytest.mark.integration


def _ready(seed):
    league = drafted_league(seed=seed)
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    presets = apply_smart_presets(league)
    league.begin_match_day(interactive=True)
    return league, league.live_match, presets


def test_begin_match_day_creates_a_live_match_at_toss(drafted):
    league = drafted
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    apply_smart_presets(league)
    league.begin_match_day(interactive=True)
    match = league.live_match
    assert match is not None
    assert match.status in ("toss", "lineup")
    assert team in (match.team1, match.team2)


def test_user_choosing_to_bat_sets_innings_order():
    league, match, _ = _ready(seed=11)
    team = league.user_team()
    force_toss(match, winner_team=team, decision="bat")
    assert match.inn1_bat == team
    assert match.inn1_bowl != team
    assert match.status == "lineup"


def test_user_choosing_to_bowl_sets_innings_order():
    league, match, _ = _ready(seed=12)
    team = league.user_team()
    force_toss(match, winner_team=team, decision="bowl")
    assert match.inn1_bowl == team
    assert match.inn1_bat != team


def test_set_user_xi_rejects_wrong_sized_xi():
    league, match, presets = _ready(seed=13)
    team = league.user_team()
    force_toss(match, winner_team=team, decision="bat")
    with pytest.raises(ValueError):
        match.set_user_xi(presets["starting_xi"][:10], context="batting")


def test_full_match_simulates_to_completion_bat_first():
    league, match, presets = _ready(seed=21)
    team = league.user_team()
    force_toss(match, winner_team=team, decision="bat")
    submit_user_xi_for_innings_role(league, match, presets)

    play_through_innings(match)
    assert match.status == "impact"
    match.apply_impact_sub()  # decline, keep it deterministic/simple
    play_through_innings(match)

    # Could be complete, or a tied match could trigger a super over.
    assert match.status in ("complete", "super_over_setup")
    if match.status == "super_over_setup":
        match.auto_missing_super_over_lineups()
        match.play_super_over()
    assert match.status == "complete"
    assert match.card is not None
    assert match.card["winner"] in (team.name, _other_team_name(match, team))


def test_full_match_simulates_to_completion_bowl_first():
    league, match, presets = _ready(seed=22)
    team = league.user_team()
    force_toss(match, winner_team=team, decision="bowl")
    submit_user_xi_for_innings_role(league, match, presets)

    play_through_innings(match)
    assert match.status == "impact"
    match.apply_impact_sub()
    # Chasing: may need to confirm a batting order before the second innings starts.
    if match.status == "batting_order":
        order_names = [p.name for p in league.smart_batting_order(match.xis[team.name])]
        match.set_user_xi([p.name for p in match.xis[team.name]], batting_order=order_names, context="bowling")
    play_through_innings(match)

    assert match.status in ("complete", "super_over_setup")
    if match.status == "super_over_setup":
        match.auto_missing_super_over_lineups()
        match.play_super_over()
    assert match.status == "complete"
    assert match.card is not None


def test_complete_live_match_advances_round_and_records_result():
    league, match, presets = _ready(seed=23)
    team = league.user_team()
    force_toss(match, winner_team=team, decision="bat")
    submit_user_xi_for_innings_role(league, match, presets)
    play_through_innings(match)
    match.apply_impact_sub()
    play_through_innings(match)
    if match.status == "super_over_setup":
        match.auto_missing_super_over_lineups()
        match.play_super_over()
    assert match.status == "complete"

    round_before = league.round_num
    league.status_message = "stale message from a previous round"
    league.complete_live_match()
    assert league.live_match is None
    assert league.round_num == round_before + 1 or league.phase == "league_complete"
    assert league.status_message != "stale message from a previous round"
    if league.phase == "season":
        assert f"Week {round_before}" in league.status_message
        assert team.name in league.status_message


def test_simulate_match_auto_runs_a_full_cpu_v_cpu_match(drafted):
    league = drafted
    t1, t2 = [t for t in league.teams if t.name != league.user_team_name][:2]
    card = league.simulate_match_auto(t1, t2, "League")
    assert card is not None
    assert card["winner"] in (t1.name, t2.name)
    assert "team1" in card and "team2" in card


def test_quick_sim_applies_default_impact_sub_for_user_team():
    """auto_finish() (quick-sim) should apply the user's default Impact Sub pairing, not decline it."""
    league, match, presets = _ready(seed=31)
    team = league.user_team()
    match.auto_finish()
    assert match.status == "complete"
    swap_out, swap_in = match.pending_swaps[team.name]
    assert swap_out and swap_in and swap_out != swap_in
    assert any(f"{swap_out} out, {swap_in} in" in entry for entry in match.impact_subs)


def _other_team_name(match, team):
    return match.team2.name if match.team1 == team else match.team1.name
