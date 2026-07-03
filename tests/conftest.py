"""Shared fixtures and helpers for the cricket-sim test suite.

Tests drive `LeagueState`/`LiveMatch` directly, exercising real game logic
without a server process.
"""
import random

import pytest

from cricket_sim_engine.sim.league_state import LeagueState

USER_TEAM = "Mumbai Mavericks"


def fresh_league(user_team=USER_TEAM, difficulty="medium", seed=12345):
    """A brand-new league, seeded for reproducibility, with the user assigned to `user_team`."""
    random.seed(seed)
    league = LeagueState()
    league.new_league(user_team, difficulty)
    return league


def drafted_league(user_team=USER_TEAM, difficulty="medium", seed=12345):
    """A league with the mega-draft fully autopiloted — every team has a full 21-player roster and the season is open."""
    league = fresh_league(user_team, difficulty, seed)
    league.start_draft()
    league.autodraft_to_end()
    return league


def player(team, name):
    """Resolve a roster member by exact name. Raises if absent — tests should fail loudly on a bad name."""
    return next(p for p in team.roster if p.name == name)


def names(players):
    return [p.name for p in players]


def resolve(team, player_names):
    return [player(team, name) for name in player_names]


def apply_smart_presets(league):
    """Build and save the Starting XI, Impact Sub, batting order, and bowling plan from the `smart_*`/`default_*` helpers — the same defaults the UI offers the user. Returns the dict of generated preset names for assertions."""
    team = league.user_team()
    starting_xi_names = league.smart_starting_xi(team)
    impact_sub_name = league.smart_impact_sub(team, starting_xi_names)
    bat_order = league.smart_batting_order(resolve(team, starting_xi_names))
    bowl_plan = league.default_bowling_plan(team)
    league.set_user_presets(
        batting_order=names(bat_order),
        bowling_order=bowl_plan,
        starting_xi=starting_xi_names,
        impact_sub_name=impact_sub_name,
    )
    return {
        "starting_xi": starting_xi_names,
        "impact_sub_name": impact_sub_name,
        "batting_order": names(bat_order),
        "bowling_plan": bowl_plan,
    }


def play_through_innings(match):
    """Auto-play overs until the live match leaves the "over" status (innings break, next-innings, or complete)."""
    while match.status == "over":
        match.play_over(auto=True, max_balls=6, stop_on_wicket=False)


def force_toss(match, winner_team, decision):
    """Override the random toss so a test can deterministically control who bats/bowls first."""
    match.toss_winner = winner_team
    match.status = "toss"
    match.choose_toss(decision)


def submit_user_xi_for_innings_role(league, match, presets):
    """Submit the user's innings-1 XI under the "11+1" model, derived via `resolve_match_xi` for whichever role (batting-first vs bowling-first) they've been assigned by the toss."""
    team = league.user_team()
    batting_first = match.inn1_bat == team
    xi_names, _swap_out, _swap_in = league.resolve_match_xi(team, batting_first)
    order = league.smart_batting_order(resolve(team, xi_names))
    context = "batting" if batting_first else "bowling"
    match.set_user_xi(
        xi_names,
        batting_order=names(order),
        bowling_order=presets["bowling_plan"],
        context=context,
        wicketkeeper_name=team.saved_wicketkeeper_name,
    )
    return xi_names, context


@pytest.fixture
def league():
    """A fresh, undrafted league for the user's team."""
    return fresh_league()


@pytest.fixture
def drafted():
    """A league with a completed mega-draft, ready to enter the season."""
    return drafted_league()


@pytest.fixture
def ready_match():
    """A drafted league with presets saved and `live_match` created, toss not yet decided."""
    league = drafted_league()
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    presets = apply_smart_presets(league)
    league.begin_match_day(interactive=True)
    return league, league.live_match, presets
