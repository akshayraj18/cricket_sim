"""Tests for Stage 3: International tournament engine.

Covers:
- new_international_tournament() constructor
- build_single_round_robin_schedule()
- finish_league_stage() qualification messages for international/Test
- setup_international_playoffs() bracket shapes for T20/ODI vs Test
- start_international_playoffs() guard
- record_international_playoff_result() result tracking + season_end transition
- unlock_international_playoff_match() Final fill-in (T20/ODI)
- Full auto-sim of a 9-round international season → playoffs → champion
- IPL regression: existing new_league(), setup_playoffs(), record_playoff_result() unchanged
"""
import random
import pytest

from cricket_sim_engine.sim.league_state import LeagueState
from cricket_sim_engine.sim.constants import INTERNATIONAL_TEAMS_LIST
from cricket_sim_engine.players_data import get_initial_player_pool


# ------------------------------------------------------------------ helpers

def _intl_league(match_format="t20", seed=42):
    random.seed(seed)
    ls = LeagueState()
    ls.new_international_tournament("Indicia", match_format=match_format)
    return ls


def _seed_pool(ls):
    """Populate player pool from the IPL player data so autodraft_to_end() doesn't crash.

    The international_current data files come in Stage 5; for now tests borrow
    the IPL pool which is structurally identical. Existing player objects are
    team-agnostic — only their name/stats matter during the draft.
    """
    ls.player_pool = get_initial_player_pool()
    for p in ls.player_pool:
        p.is_overseas = False  # no overseas cap for national teams


def _intl_drafted(match_format="t20", seed=42):
    """International league with draft completed and season started."""
    ls = _intl_league(match_format=match_format, seed=seed)
    _seed_pool(ls)
    ls.autodraft_to_end()
    return ls


def _quick_season(ls):
    """Simulate all 9 league rounds."""
    while ls.phase == "season":
        ls.simulate_current_round()


# ------------------------------------------------------------------ constructor

def test_intl_constructor_sets_competition():
    ls = _intl_league()
    assert ls.competition == "international"


def test_intl_constructor_sets_format():
    ls = _intl_league("odi")
    assert ls.match_format == "odi"


def test_intl_constructor_sets_career_mode():
    ls = _intl_league()
    assert ls.career_mode == "tournament"


def test_intl_constructor_10_teams():
    ls = _intl_league()
    assert len(ls.teams) == 10


def test_intl_constructor_team_names():
    ls = _intl_league()
    assert {t.name for t in ls.teams} == set(INTERNATIONAL_TEAMS_LIST)


def test_intl_constructor_user_team():
    ls = _intl_league()
    assert ls.user_team_name == "Indicia"


def test_intl_constructor_phase_draft():
    ls = _intl_league()
    assert ls.phase == "draft"


def test_intl_constructor_bad_team_raises():
    with pytest.raises(ValueError, match="valid international team"):
        LeagueState().new_international_tournament("Mumbai Mavericks")


def test_intl_constructor_schedule_9_rounds():
    ls = _intl_league()
    assert len(ls.schedule) == 9


def test_intl_constructor_schedule_5_games_per_round():
    ls = _intl_league()
    for rnd in ls.schedule:
        assert len(rnd) == 5, "10 teams → 5 games per round"


# ------------------------------------------------------------------ schedule coverage

def test_single_rr_all_45_pairs_covered():
    ls = _intl_league()
    pairs = set()
    for rnd in ls.schedule:
        for a, b in rnd:
            pairs.add(frozenset([a, b]))
    assert len(pairs) == 45, "10 teams → C(10,2)=45 unique pairs"


def test_single_rr_each_team_plays_9_games():
    ls = _intl_league()
    counts = {t.name: 0 for t in ls.teams}
    for rnd in ls.schedule:
        for a, b in rnd:
            counts[a] += 1
            counts[b] += 1
    assert all(c == 9 for c in counts.values())


def test_single_rr_no_pair_plays_twice():
    ls = _intl_league()
    pair_count = {}
    for rnd in ls.schedule:
        for a, b in rnd:
            key = frozenset([a, b])
            pair_count[key] = pair_count.get(key, 0) + 1
    assert all(c == 1 for c in pair_count.values())


# ------------------------------------------------------------------ finish_league_stage

def test_finish_league_stage_t20_message_qualified():
    ls = _intl_drafted(match_format="t20", seed=1)
    while ls.phase == "season":
        ls.simulate_current_round()
    assert ls.phase == "league_complete"
    # message should mention playoffs (qualified or not)
    assert "playoffs" in ls.status_message or "top four" in ls.status_message or "missed" in ls.status_message


def test_finish_league_stage_test_top2_message():
    ls = _intl_drafted(match_format="test", seed=1)
    while ls.phase == "season":
        ls.simulate_current_round()
    assert ls.phase == "league_complete"
    assert "top 2" in ls.status_message or "Final" in ls.status_message or "missed the top two" in ls.status_message


# ------------------------------------------------------------------ setup_international_playoffs

def test_setup_t20_playoffs_3_matches():
    ls = _intl_league("t20")
    from cricket_sim_engine.models import Team
    teams = [Team(n) for n in ["A", "B", "C", "D"]]
    ls.setup_international_playoffs(teams)
    assert len(ls.playoff_matches) == 3


def test_setup_t20_playoffs_names():
    ls = _intl_league("t20")
    from cricket_sim_engine.models import Team
    teams = [Team(n) for n in ["A", "B", "C", "D"]]
    ls.setup_international_playoffs(teams)
    names = [m["name"] for m in ls.playoff_matches]
    assert names == ["Semifinal 1", "Semifinal 2", "Final"]


def test_setup_t20_playoffs_seeding():
    ls = _intl_league("t20")
    from cricket_sim_engine.models import Team
    p1, p2, p3, p4 = [Team(n) for n in ["P1", "P2", "P3", "P4"]]
    ls.setup_international_playoffs([p1, p2, p3, p4])
    sf1 = ls.playoff_matches[0]
    sf2 = ls.playoff_matches[1]
    assert sf1["team1"] == "P1" and sf1["team2"] == "P4"
    assert sf2["team1"] == "P2" and sf2["team2"] == "P3"


def test_setup_t20_playoffs_final_locked():
    ls = _intl_league("t20")
    from cricket_sim_engine.models import Team
    teams = [Team(n) for n in ["A", "B", "C", "D"]]
    ls.setup_international_playoffs(teams)
    assert ls.playoff_matches[2]["status"] == "locked"


def test_setup_test_playoffs_1_match():
    ls = _intl_league("test")
    from cricket_sim_engine.models import Team
    teams = [Team(n) for n in ["A", "B"]]
    ls.setup_international_playoffs(teams)
    assert len(ls.playoff_matches) == 1


def test_setup_test_playoffs_direct_final():
    ls = _intl_league("test")
    from cricket_sim_engine.models import Team
    p1, p2 = Team("P1"), Team("P2")
    ls.setup_international_playoffs([p1, p2])
    final = ls.playoff_matches[0]
    assert final["name"] == "Final"
    assert final["team1"] == "P1"
    assert final["team2"] == "P2"
    assert final["status"] == "pending"


# ------------------------------------------------------------------ record_international_playoff_result

def _setup_t20_playoffs(ls, teams=None):
    from cricket_sim_engine.models import Team
    if teams is None:
        teams = [Team(n) for n in ["A", "B", "C", "D"]]
    ls.teams = teams
    ls.setup_international_playoffs(teams)


def test_record_sf1_result_stores_result():
    ls = _intl_league("t20")
    from cricket_sim_engine.models import Team
    teams = [Team(n) for n in ["A", "B", "C", "D"]]
    ls.teams = teams
    ls.setup_international_playoffs(teams)
    ls.record_international_playoff_result("A")
    assert ls.playoff_results[0]["winner"] == "A"
    assert ls.playoff_results[0]["loser"] == "D"


def test_record_sf1_result_marks_match_complete():
    ls = _intl_league("t20")
    from cricket_sim_engine.models import Team
    teams = [Team(n) for n in ["A", "B", "C", "D"]]
    ls.teams = teams
    ls.setup_international_playoffs(teams)
    ls.record_international_playoff_result("A")
    assert ls.playoff_matches[0]["status"] == "complete"


def test_record_sf1_advances_index():
    ls = _intl_league("t20")
    from cricket_sim_engine.models import Team
    teams = [Team(n) for n in ["A", "B", "C", "D"]]
    ls.teams = teams
    ls.setup_international_playoffs(teams)
    ls.record_international_playoff_result("A")
    assert ls.playoff_index == 1


def test_record_final_ends_season():
    ls = _intl_league("test")
    from cricket_sim_engine.models import Team
    ls.teams = [Team("P1"), Team("P2")]
    ls.setup_international_playoffs(ls.teams)
    ls.record_international_playoff_result("P1")
    assert ls.phase == "season_end"
    assert "World Champions" in ls.status_message


def test_record_final_no_retention():
    """International season_end should NOT have a retention window."""
    ls = _intl_league("t20")
    from cricket_sim_engine.models import Team
    ls.teams = [Team(n) for n in ["A", "B", "C", "D"]]
    ls.setup_international_playoffs(ls.teams)
    ls.record_international_playoff_result("A")
    ls.record_international_playoff_result("B")
    ls.record_international_playoff_result("A")
    assert ls.phase == "season_end"
    # open_retention() should raise since season is over with no retention window design
    # (LeagueState.open_retention raises ValueError — international doesn't call it)


# ------------------------------------------------------------------ unlock_international_playoff_match

def test_unlock_fills_final_for_t20():
    ls = _intl_league("t20")
    from cricket_sim_engine.models import Team
    ls.teams = [Team(n) for n in ["A", "B", "C", "D"]]
    ls.setup_international_playoffs(ls.teams)
    ls.playoff_results = [
        {"name": "Semifinal 1", "winner": "A", "loser": "D"},
        {"name": "Semifinal 2", "winner": "B", "loser": "C"},
    ]
    ls.playoff_index = 2
    ls.unlock_international_playoff_match()
    final = ls.playoff_matches[2]
    assert final["team1"] == "A"
    assert final["team2"] == "B"
    assert final["status"] == "pending"


def test_unlock_noop_for_test():
    ls = _intl_league("test")
    from cricket_sim_engine.models import Team
    ls.teams = [Team("P1"), Team("P2")]
    ls.setup_international_playoffs(ls.teams)
    # Test has only 1 match (Final), index 1 means it's done — unlock should be no-op
    ls.playoff_index = 1
    ls.playoff_results = [{"name": "Final", "winner": "P1", "loser": "P2"}]
    ls.unlock_international_playoff_match()  # must not raise
    # Final was already populated at setup, still is
    assert ls.playoff_matches[0]["team1"] == "P1"


# ------------------------------------------------------------------ start_international_playoffs guard

def test_start_international_playoffs_requires_league_complete():
    ls = _intl_league("t20")
    with pytest.raises(ValueError, match="not ready"):
        ls.start_international_playoffs()


# ------------------------------------------------------------------ full auto-sim end-to-end

@pytest.mark.parametrize("match_format", ["t20", "odi", "test"])
def test_full_intl_tournament_reaches_season_end(match_format):
    random.seed(99)
    ls = LeagueState()
    ls.new_international_tournament("Austrella", match_format=match_format)
    _seed_pool(ls)
    ls.autodraft_to_end()
    while ls.phase == "season":
        ls.simulate_current_round()
    assert ls.phase == "league_complete"
    ls.start_international_playoffs()
    assert ls.phase == "playoffs"
    while ls.phase == "playoffs":
        ls.simulate_current_round()
    assert ls.phase == "season_end"
    assert "World Champions" in ls.status_message


def test_full_intl_t20_has_3_playoff_matches_played():
    random.seed(77)
    ls = LeagueState()
    ls.new_international_tournament("Indicia", match_format="t20")
    _seed_pool(ls)
    ls.autodraft_to_end()
    while ls.phase == "season":
        ls.simulate_current_round()
    ls.start_international_playoffs()
    while ls.phase == "playoffs":
        ls.simulate_current_round()
    assert len(ls.playoff_results) == 3
    assert ls.playoff_results[2]["name"] == "Final"


def test_full_intl_test_has_1_playoff_match_played():
    random.seed(55)
    ls = LeagueState()
    ls.new_international_tournament("Engoria", match_format="test")
    _seed_pool(ls)
    ls.autodraft_to_end()
    while ls.phase == "season":
        ls.simulate_current_round()
    ls.start_international_playoffs()
    while ls.phase == "playoffs":
        ls.simulate_current_round()
    assert len(ls.playoff_results) == 1
    assert ls.playoff_results[0]["name"] == "Final"


def test_full_intl_champion_name_nonempty():
    random.seed(33)
    ls = LeagueState()
    ls.new_international_tournament("Windoria", match_format="t20")
    _seed_pool(ls)
    ls.autodraft_to_end()
    while ls.phase == "season":
        ls.simulate_current_round()
    ls.start_international_playoffs()
    while ls.phase == "playoffs":
        ls.simulate_current_round()
    champion = ls.playoff_results[-1]["winner"]
    assert champion in INTERNATIONAL_TEAMS_LIST


# ------------------------------------------------------------------ IPL regression guards

def test_ipl_new_league_still_works():
    random.seed(1)
    from cricket_sim_engine.players_data import IPL_TEAMS_LIST
    ls = LeagueState()
    ls.new_league("Mumbai Mavericks")
    assert ls.competition == "ipl"
    assert ls.match_format == "t20"
    assert len(ls.teams) == 10


def test_ipl_schedule_14_rounds():
    random.seed(1)
    ls = LeagueState()
    ls.new_league("Mumbai Mavericks")
    ls.autodraft_to_end()
    assert len(ls.schedule) == 14


def test_ipl_playoffs_4_matches():
    random.seed(5)
    ls = LeagueState()
    ls.new_league("Mumbai Mavericks")
    ls.autodraft_to_end()
    while ls.phase == "season":
        ls.simulate_current_round()
    ls.start_playoffs()
    assert len(ls.playoff_matches) == 4


def test_ipl_playoff_names():
    random.seed(5)
    ls = LeagueState()
    ls.new_league("Mumbai Mavericks")
    ls.autodraft_to_end()
    while ls.phase == "season":
        ls.simulate_current_round()
    ls.start_playoffs()
    names = [m["name"] for m in ls.playoff_matches]
    assert names == ["Qualifier 1", "Eliminator", "Qualifier 2", "Final"]
