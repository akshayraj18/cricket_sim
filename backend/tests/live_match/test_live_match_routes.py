import uuid

from httpx import AsyncClient

from cricket_sim_engine.sim.league_state import LeagueState

USER_TEAM = "Mumbai Mavericks"


async def _create_season_career(client: AsyncClient, headers: dict, **overrides) -> dict:
    body = {
        "name": "My Career",
        "user_team_name": USER_TEAM,
        "difficulty": "medium",
        "draft_pool_type": "current",
        **overrides,
    }
    resp = await client.post("/careers", json=body, headers=headers)
    assert resp.status_code == 200, resp.text
    created = resp.json()

    league = LeagueState.from_dict(created["state"])
    league.start_draft()
    league.autodraft_to_end()
    assert league.phase == "season"

    resp = await client.put(f"/careers/{created['id']}/state", json=league.to_dict(), headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _begin_match(client: AsyncClient, headers: dict, career_id: str) -> dict:
    resp = await client.post(f"/careers/{career_id}/match/begin", headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _resolve_toss_and_lineup(client: AsyncClient, headers: dict, career_id: str, payload: dict) -> dict:
    if payload["status"] == "toss":
        resp = await client.post(f"/careers/{career_id}/match/toss", json={"decision": "bat"}, headers=headers)
        assert resp.status_code == 200, resp.text
        payload = resp.json()

    while payload["status"] == "lineup":
        xi = payload["lineup_xi"]
        resp = await client.post(f"/careers/{career_id}/match/lineup", json={"xi": xi}, headers=headers)
        assert resp.status_code == 200, resp.text
        payload = resp.json()

    return payload


async def test_begin_match_requires_season_phase(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/careers", json={
        "name": "Draft Career", "user_team_name": USER_TEAM, "difficulty": "medium", "draft_pool_type": "current",
    }, headers=auth_headers)
    career = resp.json()

    resp = await client.post(f"/careers/{career['id']}/match/begin", headers=auth_headers)
    assert resp.status_code == 400


async def test_begin_match_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.post(f"/careers/{uuid.uuid4()}/match/begin", headers=auth_headers)
    assert resp.status_code == 404


async def test_get_live_match_when_none_in_progress(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)

    resp = await client.get(f"/careers/{career['id']}/match", headers=auth_headers)
    assert resp.status_code == 404


async def test_begin_match_returns_toss_or_lineup(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)

    payload = await _begin_match(client, auth_headers, career["id"])
    assert payload["status"] in ("toss", "lineup")
    assert payload["team1"] and payload["team2"]


async def test_get_live_match_after_begin(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    await _begin_match(client, auth_headers, career["id"])

    resp = await client.get(f"/careers/{career['id']}/match", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] in ("toss", "lineup")


async def test_full_lineup_and_play_over_flow(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    payload = await _begin_match(client, auth_headers, career["id"])
    payload = await _resolve_toss_and_lineup(client, auth_headers, career["id"], payload)

    assert payload["status"] == "over"
    assert payload["score"] is not None

    resp = await client.post(
        f"/careers/{career['id']}/match/play-over",
        json={"balls": 6, "stop_on_wicket": False},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["score"]["balls"] >= 6


async def test_aggression_action(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    payload = await _begin_match(client, auth_headers, career["id"])
    payload = await _resolve_toss_and_lineup(client, auth_headers, career["id"], payload)

    striker = payload["score"]["striker"]
    resp = await client.post(
        f"/careers/{career['id']}/match/aggression",
        json={"batting": {striker: 5}},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["score"]["striker_aggression"] == 5


async def test_action_requires_live_match(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)

    resp = await client.post(
        f"/careers/{career['id']}/match/toss", json={"decision": "bat"}, headers=auth_headers
    )
    assert resp.status_code == 404


async def test_unknown_action_rejected(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    await _begin_match(client, auth_headers, career["id"])

    resp = await client.post(f"/careers/{career['id']}/match/not-a-real-action", json={}, headers=auth_headers)
    assert resp.status_code == 404


async def test_invalid_toss_decision_rejected(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    payload = await _begin_match(client, auth_headers, career["id"])

    if payload["status"] != "toss":
        return  # user lost the toss this run; nothing to assert

    resp = await client.post(
        f"/careers/{career['id']}/match/toss", json={"decision": "sideways"}, headers=auth_headers
    )
    assert resp.status_code == 400


async def test_complete_match_requires_finished_match(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    await _begin_match(client, auth_headers, career["id"])

    resp = await client.post(f"/careers/{career['id']}/match/complete", headers=auth_headers)
    assert resp.status_code == 400


async def test_complete_match_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.post(f"/careers/{uuid.uuid4()}/match/complete", headers=auth_headers)
    assert resp.status_code == 404


async def test_match_isolated_per_career(client: AsyncClient, auth_headers: dict):
    career_a = await _create_season_career(client, auth_headers, name="Career A")
    career_b = await _create_season_career(client, auth_headers, name="Career B")

    await _begin_match(client, auth_headers, career_a["id"])

    resp = await client.get(f"/careers/{career_b['id']}/match", headers=auth_headers)
    assert resp.status_code == 404

    resp = await client.get(f"/careers/{career_a['id']}/match", headers=auth_headers)
    assert resp.status_code == 200


async def test_live_match_not_owned_by_user(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    await _begin_match(client, auth_headers, career["id"])

    other_resp = await client.post("/auth/guest")
    other_headers = {"Authorization": f"Bearer {other_resp.json()['tokens']['access_token']}"}

    resp = await client.get(f"/careers/{career['id']}/match", headers=other_headers)
    assert resp.status_code == 404
