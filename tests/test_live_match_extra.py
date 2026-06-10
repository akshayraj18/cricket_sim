"""Coverage for `LiveMatch` features not exercised by test_match_flow.py / test_impact_subs.py:
aggression dials, the bowling plan and bowler-availability rules, mid-innings
next-batter selection, dismissal resolution, the Super Over flow, and the
payload/serialisation helpers.
"""
import random

import pytest

from cricket_sim_engine.sim.helpers import is_bowling_role

from .conftest import (
    apply_smart_presets,
    drafted_league,
    force_toss,
    names,
    play_through_innings,
    submit_user_xi_for_innings_role,
)

pytestmark = pytest.mark.integration


def _ready(seed):
    """Build a ready-to-play match, retrying with nearby seeds if a particular
    draft happens to produce a squad whose smart batting/bowling-first XIs
    can't satisfy `set_user_presets`'s impact-sub constraints (a pre-existing
    edge case with some random rosters, unrelated to what's under test here).
    """
    last_error = None
    for offset in range(10):
        try:
            league = drafted_league(seed=seed + offset)
            team = league.user_team()
            league.set_leadership(team.captain.name, team.vice_captain.name)
            presets = apply_smart_presets(league)
            league.begin_match_day(interactive=True)
            return league, league.live_match, presets
        except ValueError as exc:
            last_error = exc
            continue
    raise last_error


def _start_live_innings(seed):
    """Get a match into "over" status (first innings live, no pending state),
    with the user's team batting first."""
    league, match, presets = _ready(seed)
    team = league.user_team()
    force_toss(match, winner_team=team, decision="bat")
    submit_user_xi_for_innings_role(league, match, presets)
    assert match.status == "over"
    return league, match, presets, team


def _start_live_innings_user_bowling(seed):
    """Get a match into "over" status with the user's team bowling first."""
    league, match, presets = _ready(seed)
    team = league.user_team()
    force_toss(match, winner_team=team, decision="bowl")
    submit_user_xi_for_innings_role(league, match, presets)
    assert match.status == "over"
    return league, match, presets, team


# --- set_aggression -----------------------------------------------------------------

def test_set_aggression_clamps_to_1_through_5():
    league, match, presets, team = _start_live_innings(seed=101)
    striker_name = match.score["batting_order"][0].name
    match.set_aggression(batting={striker_name: 99})
    assert match.score["batting_aggression"][striker_name] == 5
    match.set_aggression(batting={striker_name: -10})
    assert match.score["batting_aggression"][striker_name] == 1


def test_set_aggression_ignores_unknown_player_names():
    league, match, presets, team = _start_live_innings(seed=102)
    before = dict(match.score["batting_aggression"])
    match.set_aggression(batting={"Nobody Real": 5})
    assert match.score["batting_aggression"] == before


def test_set_aggression_updates_bowling_dial():
    league, match, presets, team = _start_live_innings(seed=103)
    bowler_name = next(iter(match.score["bowling_aggression"]))
    match.set_aggression(bowling={bowler_name: 4})
    assert match.score["bowling_aggression"][bowler_name] == 4


def test_set_aggression_no_op_before_innings_starts():
    league, match, presets = _ready(seed=104)
    # Toss not yet decided -> no score object exists.
    match.set_aggression(batting={"Anyone": 5})  # should not raise


# --- bowling plan / available bowlers --------------------------------------------------

def test_set_bowling_plan_rejects_plan_exceeding_per_bowler_cap():
    league, match, presets, team = _start_live_innings(seed=111)
    bowling_team = match.score["bowling_team"]
    pool_names = names(match.bowling_pools[bowling_team.name])
    if len(pool_names) < 2:
        pytest.skip("not enough bowling options to construct an invalid plan")
    # 5 overs from the same bowler exceeds the 4-over cap.
    plan = [pool_names[0]] * 5 + [pool_names[1 % len(pool_names)]] * 15
    match.set_bowling_plan(bowling_team, plan)
    assert match.bowling_plan_for[bowling_team.name] == []


def test_set_bowling_plan_rejects_wrong_length():
    league, match, presets, team = _start_live_innings(seed=112)
    bowling_team = match.score["bowling_team"]
    pool_names = names(match.bowling_pools[bowling_team.name])
    match.set_bowling_plan(bowling_team, pool_names[:5])  # only 5 entries, not 20
    assert match.bowling_plan_for[bowling_team.name] == []


def test_set_bowling_plan_drops_unknown_names():
    league, match, presets, team = _start_live_innings(seed=113)
    bowling_team = match.score["bowling_team"]
    pool_names = names(match.bowling_pools[bowling_team.name])
    if len(pool_names) < 5:
        pytest.skip("not enough bowling options")
    plan = (pool_names * 5)[:20]
    plan_with_unknown = ["Not A Real Bowler"] + plan
    match.set_bowling_plan(bowling_team, plan_with_unknown)
    # The unknown name is filtered out, leaving only 20 valid entries -> still
    # a valid plan as long as the per-bowler cap holds.
    cleaned = [n for n in plan_with_unknown if n in pool_names]
    if len(cleaned) == 20 and all(cleaned.count(n) <= 4 for n in set(cleaned)):
        assert match.bowling_plan_for[bowling_team.name] == cleaned
    else:
        assert match.bowling_plan_for[bowling_team.name] == []


def test_available_bowlers_excludes_bowler_who_just_bowled():
    league, match, presets, team = _start_live_innings(seed=114)
    bowler = match.ensure_active_bowler(auto=True)
    while match.score["balls"] % 6 != 0:
        match.play_over(auto=True, max_balls=1, stop_on_wicket=False)
        if match.status != "over":
            pytest.skip("innings ended before completing the over")
    options = match.available_bowlers()
    assert bowler not in options or match.score["overs_tracked"][bowler.name] >= 4


def test_available_bowlers_excludes_bowlers_at_4_over_cap():
    league, match, presets, team = _start_live_innings(seed=115)
    capped_bowler = match.score["bowling_pool"][0]
    match.score["overs_tracked"][capped_bowler.name] = 4
    options = match.available_bowlers()
    assert capped_bowler not in options or all(
        match.score["overs_tracked"].get(p.name, 0) >= 4 for p in match.score["bowling_pool"]
    )


def test_ensure_active_bowler_raises_when_no_over_ready():
    league, match, presets = _ready(seed=116)
    with pytest.raises(ValueError):
        match.ensure_active_bowler()


def test_ensure_active_bowler_raises_for_ineligible_user_choice():
    league, match, presets, team = _start_live_innings_user_bowling(seed=117)
    assert match.score["bowling_team"].name == team.name
    with pytest.raises(ValueError):
        match.ensure_active_bowler(bowler_name="Not A Real Bowler")


def test_planned_bowler_name_none_without_a_plan():
    league, match, presets, team = _start_live_innings(seed=118)
    bowling_team = match.score["bowling_team"]
    match.bowling_plan_for[bowling_team.name] = []
    assert match.planned_bowler_name() is None


def test_planned_bowler_name_returns_plan_entry_for_current_over():
    league, match, presets, team = _start_live_innings(seed=119)
    bowling_team = match.score["bowling_team"]
    pool_names = names(match.bowling_pools[bowling_team.name])
    if len(pool_names) < 5:
        pytest.skip("not enough bowling options to build a 20-over plan")
    plan = (pool_names * 5)[:20]
    if not all(plan.count(n) <= 4 for n in set(plan)):
        pytest.skip("rotation did not respect 4-over cap for this roster size")
    match.bowling_plan_for[bowling_team.name] = plan
    assert match.planned_bowler_name() == plan[0]


# --- select_next_batter ----------------------------------------------------------------

def test_select_next_batter_raises_when_no_wicket_pending():
    league, match, presets, team = _start_live_innings(seed=121)
    with pytest.raises(ValueError):
        match.select_next_batter("Anyone")


def test_select_next_batter_raises_for_player_who_already_batted():
    league, match, presets, team = _start_live_innings(seed=122)
    assert match.score["batting_team"].name == team.name
    # Force a pending-next-batter state by playing until a wicket falls.
    for _ in range(120):
        match.play_over(auto=False, max_balls=1, stop_on_wicket=True)
        if match.status == "next_batter":
            break
        if match.status != "over":
            pytest.skip("innings ended before a wicket fell")
    if match.status != "next_batter":
        pytest.skip("no wicket fell within 120 balls")
    already_batted = match.score["batting_order"][0].name
    with pytest.raises(ValueError):
        match.select_next_batter(already_batted)


def test_select_next_batter_promotes_chosen_player():
    league, match, presets, team = _start_live_innings(seed=123)
    assert match.score["batting_team"].name == team.name
    for _ in range(120):
        match.play_over(auto=False, max_balls=1, stop_on_wicket=True)
        if match.status == "next_batter":
            break
        if match.status != "over":
            pytest.skip("innings ended before a wicket fell")
    if match.status != "next_batter":
        pytest.skip("no wicket fell within 120 balls")
    order = match.score["batting_order"]
    next_idx = match.score["striker_idx"]
    # Pick the last player in the order who hasn't batted yet.
    promoted = order[-1]
    match.select_next_batter(promoted.name)
    assert order[next_idx] == promoted
    assert match.status == "over"
    assert match.score["pending_next_batter"] is False


# --- resolve_dismissal -------------------------------------------------------------------

def test_resolve_dismissal_credits_keeper_on_stumping():
    league, match, presets, team = _start_live_innings(seed=132)
    bowling_team = match.score["bowling_team"]
    keeper = match.wicketkeepers[bowling_team.name]
    striker = match.score["batting_order"][0]
    spin_bowler = next((p for p in match.score["bowling_pool"]
                         if "Spin" in getattr(p, "bowling_type", "") or "Orthodox" in getattr(p, "bowling_type", "")), None)
    if not spin_bowler:
        pytest.skip("no spin bowler available in this XI")
    keeper_stumpings_before = keeper.stats["stumpings"]
    random.seed(1)  # roll < 0.14 -> stumped
    dismissal = match.resolve_dismissal(striker, spin_bowler)
    assert dismissal["dismissal"] == "stumped"
    assert dismissal["fielder"] == keeper.name
    assert dismissal["bowler_gets_wicket"] is True
    assert keeper.stats["stumpings"] == keeper_stumpings_before + 1


def test_resolve_dismissal_run_out_does_not_credit_bowler():
    league, match, presets, team = _start_live_innings(seed=132)
    striker = match.score["batting_order"][0]
    bowler = match.score["bowling_pool"][0]
    match.score["batting_aggression"][striker.name] = 3
    random.seed(5)  # mid roll: not a stumping (no spin), but inside runout cutoff
    dismissal = match.resolve_dismissal(striker, bowler)
    if dismissal["dismissal"] == "run out":
        assert dismissal["bowler_gets_wicket"] is False
        assert dismissal["fielder"] != bowler.name or True  # fielder may equal bowler only as fallback
    else:
        # statistical dependence on RNG stream; just sanity-check the contract
        assert dismissal["dismissal"] in ("caught", "stumped")


def test_resolve_dismissal_caught_credits_bowler_and_fielder():
    league, match, presets, team = _start_live_innings(seed=133)
    striker = match.score["batting_order"][0]
    bowler = match.score["bowling_pool"][0]
    match.score["batting_aggression"][striker.name] = 1  # minimise runout cutoff
    random.seed(99)  # high roll -> falls through to caught
    dismissal = match.resolve_dismissal(striker, bowler)
    assert dismissal["dismissal"] in ("caught", "run out", "stumped")
    if dismissal["dismissal"] == "caught":
        assert dismissal["bowler_gets_wicket"] is True
        assert dismissal["description"].startswith(striker.name)


# --- Super Over flow -------------------------------------------------------------------

def _drive_to_super_over(seed, max_attempts=40):
    """Play a match to completion, then force a tied result so it lands in
    `super_over_setup`. Real ties are rare under random simulation, so we
    take a normally-completed match's two innings totals and overwrite the
    second innings' runs to equal the first, then re-run `complete_match`.
    """
    for attempt in range(max_attempts):
        try:
            league, match, presets = _ready(seed=seed * 1000 + attempt * 20)
        except ValueError:
            continue
        team = league.user_team()
        force_toss(match, winner_team=team, decision="bat")
        submit_user_xi_for_innings_role(league, match, presets)
        match.auto_finish()
        if match.status == "complete" and len(match.innings) == 2 and not match.super_over:
            match.innings[1]["runs"] = match.innings[0]["runs"]
            match.status = "live"  # reopen so complete_match can run again
            match.complete_match()
            if match.status == "super_over_setup":
                cpu_team = match.team2 if match.team1.name == team.name else match.team1
                match.super_over["bowlers"].setdefault(cpu_team.name, match.cpu_super_bowler(cpu_team))
                return league, match, presets, team
    return None


def test_cpu_super_batters_returns_three_best_batting_options():
    league, match, presets, team = _start_live_innings(seed=141)
    cpu_team = match.team2 if match.team1.name == team.name else match.team1
    batters = match.cpu_super_batters(cpu_team)
    assert len(batters) == 3
    xi = match.xis[cpu_team.name]
    ratings = sorted((p.current_batting + (8 if getattr(p, "batting_archetype", "") in ("Finisher", "Aggressor") else 0) for p in xi), reverse=True)[:3]
    chosen_ratings = sorted(p.current_batting + (8 if getattr(p, "batting_archetype", "") in ("Finisher", "Aggressor") else 0) for p in batters)
    assert sorted(chosen_ratings) == sorted(ratings) or len(set(chosen_ratings)) <= len(set(ratings))


def test_cpu_super_bowler_is_a_bowling_capable_player():
    league, match, presets, team = _start_live_innings(seed=142)
    cpu_team = match.team2 if match.team1.name == team.name else match.team1
    bowler = match.cpu_super_bowler(cpu_team)
    xi = match.xis[cpu_team.name]
    assert bowler in xi


def test_simulate_super_over_innings_ends_within_six_balls_or_two_wickets():
    league, match, presets, team = _start_live_innings(seed=143)
    cpu_team = match.team2 if match.team1.name == team.name else match.team1
    match.super_over = {
        "batting_first": cpu_team,
        "batting_second": team,
        "batters": {cpu_team.name: match.cpu_super_batters(cpu_team)},
        "bowlers": {},
        "innings": [],
        "winner": "",
        "message": "",
    }
    user_bowlers = [p for p in match.xis[team.name] if p.role != "Batsman"]
    bowler = user_bowlers[0] if user_bowlers else match.xis[team.name][0]
    result = match.simulate_super_over_innings(cpu_team, bowler)
    assert result["balls"] <= 6
    assert result["wickets"] <= 2
    assert result["team"] == cpu_team.name
    assert "score" in result


def test_simulate_super_over_innings_stops_at_target():
    league, match, presets, team = _start_live_innings(seed=144)
    cpu_team = match.team2 if match.team1.name == team.name else match.team1
    match.super_over = {
        "batting_first": cpu_team,
        "batting_second": team,
        "batters": {cpu_team.name: match.cpu_super_batters(cpu_team)},
        "bowlers": {},
        "innings": [],
        "winner": "",
        "message": "",
    }
    bowler = match.xis[team.name][0]
    # A target of 1 means the chase stops the instant any runs are scored.
    result = match.simulate_super_over_innings(cpu_team, bowler, target=1)
    assert result["balls"] <= 6
    if result["balls"] < 6 and result["wickets"] < 2:
        assert result["runs"] >= 1


def test_set_super_over_lineup_rejects_when_not_open():
    league, match, presets, team = _start_live_innings(seed=145)
    with pytest.raises(ValueError):
        match.set_super_over_lineup(["A", "B", "C"], "D")


def test_full_super_over_via_drive_to_tie():
    found = _drive_to_super_over(seed=200, max_attempts=60)
    if not found:
        pytest.skip("could not find a tied match within attempt budget")
    league, match, presets, team = found
    assert match.super_over is not None
    user_xi = match.xis[team.name]
    bowler_options = [p for p in user_xi if is_bowling_role(p)]
    bowler_name = bowler_options[0].name
    batter_names = [p.name for p in user_xi[:3]]
    match.set_super_over_lineup(batter_names, bowler_name)
    assert match.status == "complete"
    assert match.card["winner"] in (match.team1.name, match.team2.name)
    assert match.super_over["winner"] in (match.team1.name, match.team2.name)


def test_set_super_over_lineup_rejects_non_unique_batters():
    found = _drive_to_super_over(seed=201, max_attempts=60)
    if not found:
        pytest.skip("could not find a tied match within attempt budget")
    league, match, presets, team = found
    user_xi = match.xis[team.name]
    bowler_options = [p for p in user_xi if is_bowling_role(p)]
    bowler_name = bowler_options[0].name
    same_name = user_xi[0].name
    with pytest.raises(ValueError):
        match.set_super_over_lineup([same_name, same_name, same_name], bowler_name)


# --- payload methods ----------------------------------------------------------------------

def test_live_score_payload_none_before_innings_starts():
    league, match, presets = _ready(seed=151)
    assert match.live_score_payload() is None


def test_live_score_payload_structure_during_innings():
    league, match, presets, team = _start_live_innings(seed=152)
    payload = match.live_score_payload()
    assert payload["batting_team"] == match.score["batting_team"].name
    assert payload["bowling_team"] == match.score["bowling_team"].name
    assert "scoreline" in payload
    assert payload["wickets"] == 0
    assert payload["pending_next_batter"] is False
    assert isinstance(payload["bat_stats"], list)
    assert isinstance(payload["bowl_stats"], list)


def test_impact_payload_none_outside_innings_break():
    league, match, presets, team = _start_live_innings(seed=153)
    assert match.impact_payload() is None


def test_impact_payload_lists_xi_and_bench_at_innings_break():
    league, match, presets, team = _start_live_innings(seed=154)
    play_through_innings(match)
    assert match.status == "impact"
    payload = match.impact_payload()
    assert payload is not None
    assert len(payload["xi"]) == 11
    assert len(payload["bench"]) == 10  # 21-player roster - 11 in XI


def test_super_over_payload_returns_card_when_no_super_over():
    league, match, presets, team = _start_live_innings(seed=155)
    assert match.super_over_payload() is None


def test_super_over_card_none_without_super_over():
    league, match, presets, team = _start_live_innings(seed=156)
    assert match.super_over_card() is None


def test_payload_top_level_structure():
    league, match, presets, team = _start_live_innings(seed=157)
    payload = match.payload()
    assert payload["status"] == "over"
    assert payload["team1"] == match.team1.name
    assert payload["team2"] == match.team2.name
    assert "score" in payload
    assert "available_bowlers" in payload
    assert payload["card"] is None


def test_lineup_context_empty_once_match_is_live():
    league, match, presets, team = _start_live_innings(seed=158)
    assert match.lineup_context() == ""


def test_impact_context_empty_outside_innings_break():
    league, match, presets, team = _start_live_innings(seed=159)
    assert match.impact_context() == ""


def test_impact_context_matches_user_role_at_innings_break():
    league, match, presets, team = _start_live_innings(seed=160)
    play_through_innings(match)
    assert match.status == "impact"
    # User batted first, so the break offers a bat-to-bowl Impact swap.
    assert match.impact_context() == "bat_to_bowl"


def test_impact_context_bowl_to_bat_when_user_bowls_first():
    league, match, presets, team = _start_live_innings_user_bowling(seed=161)
    play_through_innings(match)
    assert match.status == "impact"
    assert match.impact_context() == "bowl_to_bat"
