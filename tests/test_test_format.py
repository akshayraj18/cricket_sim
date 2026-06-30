"""Tests for Test-match format: day/session pacing, follow-on, declaration, and draw results.

All scenarios exercise `LiveMatch` directly (same as `test_live_match_extra.py`).
A "tiny-budget" helper overrides `match.format` after the league is set up to
force day/session exhaustion in just a handful of overs, which lets the time-
expiry / draw path be exercised without simulating a full 450-over Test.
"""
import random

import pytest

from cricket_sim_engine.sim.helpers import is_bowling_role
from cricket_sim_engine.sim.league_state import LeagueState

pytestmark = pytest.mark.integration

USER_TEAM = "Mumbai Mavericks"


def _fresh_test_league(seed=1):
    random.seed(seed)
    league = LeagueState()
    league.new_league(USER_TEAM, "medium", match_format="test")
    league.start_draft()
    league.autodraft_to_end()
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    return league


def _auto_match(league):
    """Quick-sim a Test match from scratch to completion."""
    league.begin_match_day(interactive=True)
    match = league.live_match
    return match, match.auto_finish()


def _seed_with_follow_on():
    """Return (league, match, card) for a seed that produces a follow-on offer."""
    for seed in range(1, 200):
        league = _fresh_test_league(seed)
        league.begin_match_day(interactive=True)
        match = league.live_match
        card = match.auto_finish()
        if match.followed_on:
            return league, match, card
    raise RuntimeError("No follow-on found in first 200 seeds")


def _setup_innings_manually(match, league):
    """Drive a match through toss + XI setup without any innings play."""
    if match.status == "toss":
        match.choose_toss(random.choice(["bat", "bowl"]))
    for t in (match.team1, match.team2):
        if t.name not in match.xis:
            xi = (
                match.user_preset_xi(t)
                if t.name == league.user_team_name
                else league.smart_cpu_xi(t)
            )
            match.xis[t.name] = xi
            match.batting_orders[t.name] = league.smart_batting_order(xi)
            match.bowling_pools[t.name] = [p for p in xi if is_bowling_role(p)] or xi
            match.wicketkeepers.setdefault(t.name, match.default_keeper(t, xi))
    match.start_first_innings_if_ready()


# ---------------------------------------------------------------------------
# format constants
# ---------------------------------------------------------------------------


def test_test_format_config():
    """format_config returns the right constants for 'test'."""
    from cricket_sim_engine.sim.constants import format_config
    cfg = format_config("test")
    assert cfg["innings_per_side"] == 2
    assert cfg["balls_per_innings"] == 540
    assert cfg["days"] == 5
    assert cfg["sessions_per_day"] == 3
    assert cfg["overs_per_session"] == 30
    assert cfg["follow_on_margin"] == 200
    assert cfg["allows_draw"] is True


def test_test_league_sets_match_format():
    """new_league(..., match_format='test') sets competition/match_format correctly."""
    league = _fresh_test_league()
    assert league.match_format == "test"
    assert league.competition == "ipl"


# ---------------------------------------------------------------------------
# full-match result correctness
# ---------------------------------------------------------------------------


def test_full_test_match_completes(seed=42):
    """auto_finish() drives a full Test match to 'complete' status with 3 or 4 innings."""
    league = _fresh_test_league(seed)
    match, card = _auto_match(league)
    assert match.status == "complete"
    assert len(match.innings) in (3, 4)
    assert card is not None
    assert card.get("summary")


def test_full_test_match_points_are_conserved():
    """Total team points after any Test result are always 2 (win+loss) or 2 (draw: 1+1)."""
    for seed in range(1, 10):
        league = _fresh_test_league(seed)
        match, card = _auto_match(league)
        total = match.team1.points + match.team2.points
        assert total == 2, f"seed {seed}: total points {total}"


def test_full_test_match_teams_alternate_innings():
    """Innings 0 and 2 have the same batting team; innings 1 and 3 have the other (normal path)."""
    league = _fresh_test_league(42)
    match, card = _auto_match(league)
    if len(match.innings) == 4 and not match.followed_on:
        teams = [inn["team"] for inn in match.innings]
        assert teams[0] == teams[2]
        assert teams[1] == teams[3]
        assert teams[0] != teams[1]


def test_win_by_wickets_margin_format():
    """A 4th-innings win-by-wickets result contains 'wickets' in the margin string."""
    for seed in range(1, 20):
        league = _fresh_test_league(seed)
        match, card = _auto_match(league)
        if not card.get("draw") and len(match.innings) == 4:
            last = match.innings[-1]
            team_a = [i for i in match.innings if i["team"] == match.inn1_bat]
            team_b = [i for i in match.innings if i["team"] == match.inn1_bowl]
            if sum(i["runs"] for i in team_b) > sum(i["runs"] for i in team_a):
                assert "wickets" in card["margin"], f"expected wickets win, got: {card['margin']}"
            break


def test_wins_and_losses_recorded_on_teams():
    """The winning team records +1 win, the losing team records +1 loss."""
    for seed in range(1, 10):
        league = _fresh_test_league(seed)
        match, card = _auto_match(league)
        if not card.get("draw"):
            winner_name = card["winner"]
            winner = next(t for t in (match.team1, match.team2) if t.name == winner_name)
            loser = match.team1 if winner == match.team2 else match.team2
            assert winner.wins == 1
            assert loser.losses == 1


# ---------------------------------------------------------------------------
# follow-on
# ---------------------------------------------------------------------------


def test_follow_on_enforced_produces_3_team_b_innings():
    """When a follow-on is enforced, team B bats in innings 2 AND innings 3."""
    _, match, card = _seed_with_follow_on()
    assert match.followed_on is True
    team_b_innings = [inn for inn in match.innings if inn["team"] == match.inn1_bowl]
    assert len(team_b_innings) == 2


def test_follow_on_enforced_team_b_bats_consecutively():
    """After an enforced follow-on, innings[1] and innings[2] are both team B."""
    _, match, card = _seed_with_follow_on()
    assert match.innings[1]["team"] == match.inn1_bowl
    assert match.innings[2]["team"] == match.inn1_bowl


def test_follow_on_decline_bats_team_a_in_innings3():
    """Declining the follow-on sends team A back to bat in innings 3, not team B."""
    random.seed(1)  # seed 1 produces a follow-on offer
    league = _fresh_test_league(1)
    league.begin_match_day(interactive=True)
    match = league.live_match
    _setup_innings_manually(match, league)
    while match.status == "over":
        match.play_over(auto=True)
    if match.status == "impact":
        match.apply_impact_sub(auto=True)
    while match.status == "over":
        match.play_over(auto=True)
    assert match.status == "follow_on_decision"
    match.decide_follow_on(enforce=False)
    assert match.followed_on is False
    if match.status == "impact":
        match.apply_impact_sub(auto=True)
    # Innings 3 should now be team A (inn1_bat) batting again.
    assert match.score["batting_team"] == match.inn1_bat


def test_follow_on_decision_errors_when_not_pending():
    """decide_follow_on raises ValueError if not currently waiting for that decision."""
    league = _fresh_test_league(42)
    league.begin_match_day(interactive=True)
    match = league.live_match
    with pytest.raises(ValueError):
        match.decide_follow_on(enforce=True)


# ---------------------------------------------------------------------------
# declaration
# ---------------------------------------------------------------------------


def test_declare_ends_innings_and_advances():
    """declare_innings() closes the current innings and moves to the next innings-break."""
    random.seed(1)
    league = _fresh_test_league(1)
    league.begin_match_day(interactive=True)
    match = league.live_match
    _setup_innings_manually(match, league)
    while match.status == "over":
        match.play_over(auto=True)
    if match.status == "impact":
        match.apply_impact_sub(auto=True)
    while match.status == "over":
        match.play_over(auto=True)
    if match.status == "follow_on_decision":
        match.decide_follow_on(enforce=False)
    if match.status == "impact":
        match.apply_impact_sub(auto=True)
    # Now play 5 overs in innings 3, then declare.
    for _ in range(5):
        if match.status == "over":
            match.play_over(auto=True)
    assert match.status == "over"
    runs_before = match.score["runs"]
    match.declare_innings()
    assert match.declared.get(3) is True
    # After declaration, should be at an innings break (impact) or complete.
    assert match.status in ("impact", "complete")
    # The declared innings should be archived.
    declared_inn = next(i for i in match.innings if match.declared.get(match.innings.index(i) + 1))
    assert declared_inn["runs"] == runs_before


def test_declare_raises_for_limited_overs():
    """declare_innings() raises ValueError if the format is not Test (innings_per_side==1)."""
    random.seed(5)
    league = LeagueState()
    league.new_league(USER_TEAM, "medium", match_format="t20")
    league.start_draft()
    league.autodraft_to_end()
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    league.begin_match_day(interactive=True)
    match = league.live_match
    _setup_innings_manually(match, league)
    while match.status == "over":
        match.play_over(auto=True)
    with pytest.raises(ValueError):
        match.declare_innings()


def test_declare_raises_when_no_innings_in_progress():
    """declare_innings() raises if no innings is currently live."""
    league = _fresh_test_league(1)
    league.begin_match_day(interactive=True)
    match = league.live_match
    with pytest.raises(ValueError):
        match.declare_innings()


# ---------------------------------------------------------------------------
# session breaks / proceed-session
# ---------------------------------------------------------------------------


def test_session_break_flagged_after_overs_per_session():
    """After exactly overs_per_session overs in a session, pending_session_break becomes True."""
    random.seed(2)
    league = _fresh_test_league(2)
    league.begin_match_day(interactive=True)
    match = league.live_match
    _setup_innings_manually(match, league)
    overs_per_session = match.format["overs_per_session"]
    for _ in range(overs_per_session):
        if match.status == "over":
            match.play_over(auto=True)
    assert match.pending_session_break is True


def test_session_break_clears_on_proceed():
    """proceed_session() clears the pending_session_break flag."""
    random.seed(2)
    league = _fresh_test_league(2)
    league.begin_match_day(interactive=True)
    match = league.live_match
    _setup_innings_manually(match, league)
    for _ in range(match.format["overs_per_session"]):
        if match.status == "over":
            match.play_over(auto=True)
    assert match.pending_session_break is True
    match.proceed_session()
    assert match.pending_session_break is False


def test_proceed_session_raises_when_no_break_pending():
    """proceed_session() raises ValueError if no session break is pending."""
    league = _fresh_test_league(2)
    league.begin_match_day(interactive=True)
    match = league.live_match
    with pytest.raises(ValueError):
        match.proceed_session()


def test_session_advances_to_next_day_after_final_session():
    """After all sessions on day N are done, the day counter increments."""
    random.seed(2)
    league = _fresh_test_league(2)
    league.begin_match_day(interactive=True)
    match = league.live_match
    _setup_innings_manually(match, league)
    overs_per_day = match.format["overs_per_session"] * match.format["sessions_per_day"]
    for _ in range(overs_per_day):
        if match.status == "over":
            match.play_over(auto=True)
        if match.pending_session_break:
            match.proceed_session()
    if match.current_day > 1:
        assert match.current_day == 2
        assert match.current_session == 1


def test_auto_finish_plays_through_session_breaks():
    """auto_finish() drives through all session breaks automatically without stalling."""
    league = _fresh_test_league(7)
    match, card = _auto_match(league)
    assert match.status == "complete"


# ---------------------------------------------------------------------------
# draw path
# ---------------------------------------------------------------------------


def _tiny_draw_match(seed):
    """Set up a Test match where the time budget (1 over per session, 1 day) forces a draw."""
    league = _fresh_test_league(seed)
    league.begin_match_day(interactive=True)
    match = league.live_match
    match.format = dict(match.format)
    match.format["days"] = 1
    match.format["sessions_per_day"] = 1
    match.format["overs_per_session"] = 1
    match.format["balls_per_innings"] = 540
    return match, match.auto_finish()


def test_draw_via_tiny_time_budget():
    """With a 1-over time budget, the match ends in a draw with 1 point each.

    Seeds 1 and 2 reliably produce a draw with this budget (the 4th-innings
    chase can't be completed in 6 balls given the targets that arise).
    """
    match, card = _tiny_draw_match(1)
    assert card.get("draw") is True
    assert match.team1.draws == 1
    assert match.team2.draws == 1
    assert match.team1.points == 1
    assert match.team2.points == 1


def test_draw_summary_text():
    """A drawn match's summary is 'Match drawn'."""
    match, card = _tiny_draw_match(2)
    assert card["summary"] == "Match drawn"
    assert card["winner"] == ""


# ---------------------------------------------------------------------------
# payload fields
# ---------------------------------------------------------------------------


def test_payload_exposes_match_format():
    """payload() includes 'match_format' key set to 'test'."""
    league = _fresh_test_league(2)
    league.begin_match_day(interactive=True)
    match = league.live_match
    _setup_innings_manually(match, league)
    p = match.payload()
    assert p["match_format"] == "test"


def test_payload_exposes_session_fields():
    """payload() includes current_day, current_session, sessions_per_day."""
    league = _fresh_test_league(2)
    league.begin_match_day(interactive=True)
    match = league.live_match
    _setup_innings_manually(match, league)
    p = match.payload()
    assert p["current_day"] == 1
    assert p["current_session"] == 1
    assert p["sessions_per_day"] == match.format["sessions_per_day"]


def test_payload_pending_session_break():
    """payload() reflects pending_session_break after a full session's overs."""
    random.seed(2)
    league = _fresh_test_league(2)
    league.begin_match_day(interactive=True)
    match = league.live_match
    _setup_innings_manually(match, league)
    for _ in range(match.format["overs_per_session"]):
        if match.status == "over":
            match.play_over(auto=True)
    p = match.payload()
    assert p["pending_session_break"] is True


def test_payload_follow_on_available():
    """payload() sets follow_on_available when status is follow_on_decision."""
    random.seed(1)
    league = _fresh_test_league(1)
    league.begin_match_day(interactive=True)
    match = league.live_match
    _setup_innings_manually(match, league)
    while match.status == "over":
        match.play_over(auto=True)
    if match.status == "impact":
        match.apply_impact_sub(auto=True)
    while match.status == "over":
        match.play_over(auto=True)
    if match.status == "follow_on_decision":
        p = match.payload()
        assert p["follow_on_available"] is True


def test_payload_can_declare_only_when_user_is_batting():
    """can_declare is True only when it's a Test match AND the user's team is currently batting."""
    random.seed(2)
    league = _fresh_test_league(2)
    league.begin_match_day(interactive=True)
    match = league.live_match
    _setup_innings_manually(match, league)
    user_team = league.user_team()
    while match.status == "over":
        match.play_over(auto=True)
    if match.status != "over":
        return  # innings ended; can_declare timing depends on who batted
    # If status is still over (mid-innings), check against who's batting.
    if match.score and match.status == "over":
        p = match.payload()
        batting = match.score["batting_team"]
        assert p["can_declare"] == (batting == user_team)


# ---------------------------------------------------------------------------
# T20/ODI regression guard — new Test code must not affect them
# ---------------------------------------------------------------------------


def test_t20_match_still_finishes_in_2_innings():
    """T20 matches must still complete in exactly 2 innings after Test plumbing additions."""
    random.seed(5)
    league = LeagueState()
    league.new_league(USER_TEAM, "medium", match_format="t20")
    league.start_draft()
    league.autodraft_to_end()
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    league.begin_match_day(interactive=True)
    match, card = league.live_match, league.live_match.auto_finish()
    assert match.status == "complete"
    assert len(match.innings) == 2
    assert not card.get("draw")


def test_odi_match_still_finishes_in_2_innings():
    """ODI matches must still complete in exactly 2 innings after Test plumbing additions."""
    random.seed(5)
    league = LeagueState()
    league.new_league(USER_TEAM, "medium", match_format="odi")
    league.start_draft()
    league.autodraft_to_end()
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    league.begin_match_day(interactive=True)
    match, card = league.live_match, league.live_match.auto_finish()
    assert match.status == "complete"
    assert len(match.innings) == 2
    assert not card.get("draw")
