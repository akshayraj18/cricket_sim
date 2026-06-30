"""Tests for Stage 4: Bilateral series engine."""
import random
import pytest

from cricket_sim_engine.sim.league_state import LeagueState
from cricket_sim_engine.sim.constants import INTERNATIONAL_TEAMS_LIST
from cricket_sim_engine.players_data import get_initial_player_pool


def _seed_pool(ls):
    ls.player_pool = get_initial_player_pool()
    for p in ls.player_pool:
        p.is_overseas = False


def _bilateral(user="Indicia", opp="Austrella", fmt="t20", n=3, seed=42):
    random.seed(seed)
    ls = LeagueState()
    ls.new_bilateral_series(user, opp, match_format=fmt, series_length=n)
    _seed_pool(ls)
    ls.autodraft_to_end()
    return ls


def _play_series(ls):
    while ls.phase == "season":
        ls.simulate_current_round()


# ------------------------------------------------------------------ constructor

def test_bilateral_sets_competition():
    ls = _bilateral()
    assert ls.competition == "international"

def test_bilateral_sets_career_mode():
    ls = _bilateral()
    assert ls.career_mode == "bilateral"

def test_bilateral_sets_format():
    ls = _bilateral(fmt="odi")
    assert ls.match_format == "odi"

def test_bilateral_sets_series_length():
    ls = _bilateral(n=5)
    assert ls.series_length == 5

def test_bilateral_2_teams_only():
    ls = _bilateral()
    assert len(ls.teams) == 2

def test_bilateral_team_names():
    ls = _bilateral("Indicia", "Austrella")
    assert {t.name for t in ls.teams} == {"Indicia", "Austrella"}

def test_bilateral_user_team():
    ls = _bilateral("Engoria", "Nustria")
    assert ls.user_team_name == "Engoria"

def test_bilateral_bad_user_team_raises():
    with pytest.raises(ValueError, match="valid international team"):
        LeagueState().new_bilateral_series("Mumbai Mavericks", "Indicia")

def test_bilateral_bad_opponent_raises():
    with pytest.raises(ValueError, match="valid opponent"):
        LeagueState().new_bilateral_series("Indicia", "Mumbai Mavericks")

def test_bilateral_same_team_raises():
    with pytest.raises(ValueError, match="different"):
        LeagueState().new_bilateral_series("Indicia", "Indicia")

def test_bilateral_invalid_length_raises():
    with pytest.raises(ValueError, match="1, 3, or 5"):
        LeagueState().new_bilateral_series("Indicia", "Austrella", series_length=2)

def test_bilateral_no_schedule():
    ls = _bilateral()
    assert ls.schedule == []

def test_bilateral_starts_in_draft():
    random.seed(1)
    ls = LeagueState()
    ls.new_bilateral_series("Indicia", "Austrella")
    assert ls.phase == "draft"


# ------------------------------------------------------------------ series completion logic

def test_series_not_complete_at_start():
    ls = _bilateral(n=3)
    ls.bilateral_wins = {"Indicia": 0, "Austrella": 0}
    ls.bilateral_match_num = 0
    assert not ls.bilateral_series_complete()

def test_series_complete_when_target_reached():
    ls = _bilateral(n=3)
    ls.bilateral_wins = {"Indicia": 2, "Austrella": 0}
    ls.bilateral_match_num = 2
    assert ls.bilateral_series_complete()

def test_series_complete_when_all_played():
    ls = _bilateral(n=3)
    ls.bilateral_wins = {"Indicia": 1, "Austrella": 1}
    ls.bilateral_match_num = 3
    assert ls.bilateral_series_complete()

def test_series_winner_majority():
    ls = _bilateral(n=3)
    ls.bilateral_wins = {"Indicia": 2, "Austrella": 0}
    assert ls.bilateral_series_winner() == "Indicia"

def test_series_winner_empty_on_tie():
    ls = _bilateral(n=3)
    # manually set a tie scenario (1 win each after 2 matches)
    ls.bilateral_wins = {"Indicia": 1, "Austrella": 1}
    ls.bilateral_match_num = 3  # all 3 played, still 1-1 (one was a draw)
    assert ls.bilateral_series_winner() == ""

def test_series_1_match_winner():
    ls = _bilateral(n=1)
    ls.bilateral_wins = {"Indicia": 1, "Austrella": 0}
    assert ls.bilateral_series_complete()
    assert ls.bilateral_series_winner() == "Indicia"


# ------------------------------------------------------------------ full auto-sim

@pytest.mark.parametrize("n", [1, 3, 5])
def test_bilateral_reaches_season_end(n):
    random.seed(11)
    ls = LeagueState()
    ls.new_bilateral_series("Indicia", "Austrella", series_length=n)
    _seed_pool(ls)
    ls.autodraft_to_end()
    _play_series(ls)
    assert ls.phase == "season_end"

def test_bilateral_status_message_has_score():
    ls = _bilateral(n=3, seed=7)
    _play_series(ls)
    msg = ls.status_message
    assert "-" in msg  # e.g. "2-1" or "2-0"

def test_bilateral_at_most_series_length_matches():
    ls = _bilateral(n=3, seed=99)
    _play_series(ls)
    assert ls.bilateral_match_num <= 3

def test_bilateral_5match_no_more_than_5():
    ls = _bilateral(n=5, seed=77)
    _play_series(ls)
    assert ls.bilateral_match_num <= 5

def test_bilateral_early_exit_best_of_3():
    """Series of 3 should stop at 2 wins for the leader."""
    ls = _bilateral(n=3, seed=42)
    _play_series(ls)
    wins = list(ls.bilateral_wins.values())
    assert max(wins) >= 2 or ls.bilateral_match_num == 3

def test_bilateral_fixture_results_recorded():
    ls = _bilateral(n=3, seed=5)
    _play_series(ls)
    assert len(ls.fixture_results) == ls.bilateral_match_num

def test_bilateral_payload_has_bilateral_fields():
    ls = _bilateral(n=3)
    p = ls.payload()
    assert p["career_mode"] == "bilateral"
    assert p["series_length"] == 3
    assert "bilateral_wins" in p
    assert "bilateral_match_num" in p

def test_bilateral_payload_competition():
    ls = _bilateral()
    assert ls.payload()["competition"] == "international"

def test_bilateral_no_playoffs():
    ls = _bilateral(n=3, seed=3)
    _play_series(ls)
    # bilateral series ends at season_end with no playoffs phase
    assert ls.playoff_matches == []

@pytest.mark.parametrize("fmt", ["t20", "odi", "test"])
def test_bilateral_all_formats_complete(fmt):
    random.seed(55)
    ls = LeagueState()
    ls.new_bilateral_series("Indicia", "Pakoria", match_format=fmt, series_length=1)
    _seed_pool(ls)
    ls.autodraft_to_end()
    _play_series(ls)
    assert ls.phase == "season_end"
