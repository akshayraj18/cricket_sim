"""HTTP integration tests for `ui_server.py`.

Spins up the real `Handler` on an ephemeral port (a `ThreadingHTTPServer`,
same as production) and drives it with plain HTTP requests, exercising
`/api/state`, `/api/saves`, static file serving (including path-traversal
rejection), and a representative slice of the `/api/<action>` POST dispatch
table — including its blanket exception-to-400 handling.
"""
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from legacy import ui_server

from .conftest import USER_TEAM, drafted_league, fresh_league

pytestmark = pytest.mark.integration


@pytest.fixture
def server():
    """Run the real Handler on an ephemeral local port for the duration of one test."""
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), ui_server.Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:
        yield base_url
    finally:
        httpd.shutdown()
        thread.join()


def get(base_url, path):
    with urllib.request.urlopen(base_url + path) as resp:
        return resp.status, json.loads(resp.read())


def post(base_url, path, payload=None):
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(base_url + path, data=data, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


# --- GET /api/state and /api/saves ---------------------------------------------------

def test_get_api_state_returns_current_payload(server):
    ui_server.replace_state(fresh_league())
    status, data = get(server, "/api/state")
    assert status == 200
    assert data["phase"] == "draft"
    assert data["user_team"] == USER_TEAM


def test_get_api_state_does_not_mutate_state(server):
    ui_server.replace_state(fresh_league())
    before = ui_server.STATE.payload()
    get(server, "/api/state")
    after = ui_server.STATE.payload()
    assert before["phase"] == after["phase"]
    assert before["draft"]["round"] == after["draft"]["round"]


def test_get_api_saves_returns_list(server, tmp_path, monkeypatch):
    monkeypatch.setattr("cricket_sim_engine.sim.league_state.SAVES_DIR", str(tmp_path / "saves"))
    status, data = get(server, "/api/saves")
    assert status == 200
    assert data["saves"] == []


# --- static file serving ----------------------------------------------------------------

def test_get_root_serves_index_html(server):
    with urllib.request.urlopen(server + "/") as resp:
        assert resp.status == 200
        assert resp.headers["Content-Type"].startswith("text/html")
        body = resp.read().decode("utf-8")
    assert "<html" in body.lower()


def test_get_static_asset_serves_app_js(server):
    with urllib.request.urlopen(server + "/app.js") as resp:
        assert resp.status == 200
        assert "javascript" in resp.headers["Content-Type"]


def test_get_unknown_static_path_returns_404(server):
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(server + "/does-not-exist.xyz")
    assert exc_info.value.code == 404


def test_get_path_traversal_is_rejected(server):
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(server + "/../ui_server.py")
    assert exc_info.value.code == 404


def test_get_unknown_api_path_falls_through_to_static_404(server):
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(server + "/api/not-a-real-endpoint")
    assert exc_info.value.code == 404


# --- POST error handling -----------------------------------------------------------------

def test_post_unknown_action_returns_404(server):
    data = json.dumps({}).encode("utf-8")
    req = urllib.request.Request(server + "/api/totally-bogus-action", data=data, method="POST")
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 404


def test_post_action_exception_returns_400_with_error_message(server):
    ui_server.replace_state(fresh_league())
    # Drafting a player not in the pool raises inside LeagueState.user_pick.
    status, data = post(server, "/api/draft", {"player": "Nobody Real"})
    assert status == 400
    assert "error" in data


def test_post_toss_without_live_match_returns_400(server):
    ui_server.replace_state(fresh_league())
    status, data = post(server, "/api/toss", {"decision": "bat"})
    assert status == 400
    assert "error" in data


# --- POST /api/new -----------------------------------------------------------------------

def test_post_new_current_pool_starts_draft_phase(server):
    status, data = post(server, "/api/new", {"team": USER_TEAM, "difficulty": "medium", "draft_pool": "current"})
    assert status == 200
    assert data["phase"] == "draft"
    assert data["draft_pool_type"] == "current"
    assert data["user_team"] == USER_TEAM


def test_post_new_alltime_pool_sets_draft_pool_type(server):
    status, data = post(server, "/api/new", {"team": USER_TEAM, "difficulty": "medium", "draft_pool": "alltime"})
    assert status == 200
    assert data["draft_pool_type"] == "alltime"


def test_post_new_rosters2026_starts_season_phase(server):
    status, data = post(server, "/api/new", {"team": USER_TEAM, "difficulty": "medium", "draft_pool": "rosters2026"})
    assert status == 200
    assert data["phase"] == "season"
    assert data["draft_pool_type"] == "rosters2026"


# --- draft flow -----------------------------------------------------------------------

def test_post_start_draft_then_autodraft_all_completes_draft(server):
    post(server, "/api/new", {"team": USER_TEAM, "difficulty": "medium", "draft_pool": "current"})
    status, data = post(server, "/api/start-draft")
    assert status == 200
    status, data = post(server, "/api/autodraft", {"mode": "all"})
    assert status == 200
    assert data["phase"] == "season"
    user_team = next(t for t in data["teams"] if t["name"] == USER_TEAM)
    assert len(user_team["roster"]) == 21


def test_post_draft_user_pick(server):
    post(server, "/api/new", {"team": USER_TEAM, "difficulty": "medium", "draft_pool": "current"})
    post(server, "/api/start-draft")
    status, data = get(server, "/api/state")
    available = data["draft"]["available"]
    pick_name = available[0]["name"]
    status, data = post(server, "/api/draft", {"player": pick_name})
    assert status == 200
    user_team = next(t for t in data["teams"] if t["name"] == USER_TEAM)
    assert pick_name in [p["name"] for p in user_team["roster"]]


# --- save / load / delete --------------------------------------------------------------

def test_save_load_delete_round_trip(server, tmp_path, monkeypatch):
    monkeypatch.setattr("cricket_sim_engine.sim.league_state.SAVES_DIR", str(tmp_path / "saves"))
    monkeypatch.setattr("cricket_sim_engine.sim.league_state.SAVE_FILE", str(tmp_path / "legacy.pkl"))
    ui_server.replace_state(fresh_league())

    status, data = post(server, "/api/save", {"name": "Integration Test Save"})
    assert status == 200

    status, data = get(server, "/api/saves")
    assert status == 200
    names = [s["name"] for s in data["saves"]]
    assert "Integration Test Save" in names

    ui_server.replace_state(fresh_league(seed=999))
    status, data = post(server, "/api/load", {"name": "Integration Test Save"})
    assert status == 200
    assert ui_server.STATE.user_team_name == USER_TEAM

    status, data = post(server, "/api/delete-save", {"name": "Integration Test Save"})
    assert status == 200
    status, data = get(server, "/api/saves")
    assert "Integration Test Save" not in [s["name"] for s in data["saves"]]


def test_load_nonexistent_save_returns_400(server, tmp_path, monkeypatch):
    monkeypatch.setattr("cricket_sim_engine.sim.league_state.SAVES_DIR", str(tmp_path / "saves"))
    monkeypatch.setattr("cricket_sim_engine.sim.league_state.SAVE_FILE", str(tmp_path / "legacy.pkl"))
    status, data = post(server, "/api/load", {"name": "No Such Save"})
    assert status == 400
    assert "error" in data


# --- season-phase actions: leadership, presets, retention ------------------------------

def test_post_leadership_and_presets(server):
    ui_server.replace_state(drafted_league())
    league = ui_server.STATE
    team = league.user_team()
    status, data = post(server, "/api/leadership", {"captain": team.captain.name, "vice": team.vice_captain.name})
    assert status == 200

    starting_xi = league.smart_starting_xi(team)
    impact_sub_name = league.smart_impact_sub(team, starting_xi)
    bat_order_names = [p.name for p in league.smart_batting_order([next(p for p in team.roster if p.name == n) for n in starting_xi])]
    bowl_plan = league.default_bowling_plan(team)
    status, data = post(server, "/api/presets", {
        "batting_order": bat_order_names,
        "bowling_order": bowl_plan,
        "starting_xi": starting_xi,
        "impact_sub_name": impact_sub_name,
    })
    assert status == 200


def test_post_begin_match_creates_live_match(server):
    league = drafted_league()
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    ui_server.replace_state(league)
    status, data = post(server, "/api/begin-match")
    assert status == 200
    assert data["live_match"] is not None
    assert data["live_match"]["status"] in ("toss", "lineup")


# --- live match actions: toss, lineup, aggression ---------------------------------------

def test_post_toss_decision(server):
    league = drafted_league()
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    league.begin_match_day(interactive=True)
    match = league.live_match
    # Force the user to have won the toss so /api/toss is the open action.
    match.toss_winner = team
    match.status = "toss"
    ui_server.replace_state(league)
    status, data = post(server, "/api/toss", {"decision": "bat"})
    assert status == 200
    assert data["live_match"]["status"] == "lineup"


def test_post_aggression_updates_live_score(server):
    league = drafted_league()
    team = league.user_team()
    league.set_leadership(team.captain.name, team.vice_captain.name)
    presets_team = league.user_team()
    starting_xi_names = league.smart_starting_xi(presets_team)
    impact_sub_name = league.smart_impact_sub(presets_team, starting_xi_names)
    bat_order = league.smart_batting_order([next(p for p in presets_team.roster if p.name == n) for n in starting_xi_names])
    bowl_plan = league.default_bowling_plan(presets_team)
    league.set_user_presets(
        batting_order=[p.name for p in bat_order],
        bowling_order=bowl_plan,
        starting_xi=starting_xi_names,
        impact_sub_name=impact_sub_name,
    )
    league.begin_match_day(interactive=True)
    match = league.live_match
    match.toss_winner = team
    match.status = "toss"
    match.choose_toss("bat")
    xi = league.smart_starting_xi(team)
    order = league.smart_batting_order([next(p for p in team.roster if p.name == n) for n in xi])
    match.set_user_xi(xi, batting_order=[p.name for p in order], bowling_order=bowl_plan, context="batting", wicketkeeper_name=team.saved_wicketkeeper_name)
    assert match.status == "over"
    ui_server.replace_state(league)

    striker_name = match.score["batting_order"][0].name
    status, data = post(server, "/api/aggression", {"batting": {striker_name: 5}})
    assert status == 200
    assert data["live_match"]["score"]["striker_aggression"] == 5
