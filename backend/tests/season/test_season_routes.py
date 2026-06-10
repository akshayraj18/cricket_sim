import uuid

from httpx import AsyncClient

USER_TEAM = "Mumbai Indians"


async def _create_draft_career(client: AsyncClient, headers: dict, **overrides) -> dict:
    body = {
        "name": "My Career",
        "user_team_name": USER_TEAM,
        "difficulty": "medium",
        "draft_pool_type": "current",
        **overrides,
    }
    resp = await client.post("/careers", json=body, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _create_season_career(client: AsyncClient, headers: dict, **overrides) -> dict:
    return await _create_draft_career(client, headers, draft_pool_type="rosters2026", **overrides)


async def test_get_payload(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)

    resp = await client.get(f"/careers/{career['id']}/payload", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["phase"] == "season"
    assert payload["user_team"] == USER_TEAM
    assert len(payload["teams"]) == 10


async def test_get_payload_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"/careers/{uuid.uuid4()}/payload", headers=auth_headers)
    assert resp.status_code == 404


async def test_draft_flow(client: AsyncClient, auth_headers: dict):
    career = await _create_draft_career(client, auth_headers)
    career_id = career["id"]

    resp = await client.post(f"/careers/{career_id}/draft/start", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["draft"]["started"] is True
    assert payload["draft"]["current_team"] == USER_TEAM

    player_name = payload["draft"]["available"][0]["name"]
    resp = await client.post(
        f"/careers/{career_id}/draft/pick", json={"player_name": player_name}, headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    user_team_dict = next(t for t in payload["teams"] if t["name"] == USER_TEAM)
    assert any(p["name"] == player_name for p in user_team_dict["roster"])

    resp = await client.post(
        f"/careers/{career_id}/draft/autodraft", json={"mode": "all"}, headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["phase"] == "season"


async def test_draft_pick_invalid_player(client: AsyncClient, auth_headers: dict):
    career = await _create_draft_career(client, auth_headers)
    career_id = career["id"]
    await client.post(f"/careers/{career_id}/draft/start", headers=auth_headers)

    resp = await client.post(
        f"/careers/{career_id}/draft/pick", json={"player_name": "Not A Real Player"}, headers=auth_headers
    )
    assert resp.status_code == 400


async def test_set_leadership(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    career_id = career["id"]

    resp = await client.get(f"/careers/{career_id}/payload", headers=auth_headers)
    user_team = next(t for t in resp.json()["teams"] if t["name"] == USER_TEAM)
    roster_names = [p["name"] for p in user_team["roster"]]

    resp = await client.post(
        f"/careers/{career_id}/leadership",
        json={"captain": roster_names[0], "vice": roster_names[1]},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    user_team = next(t for t in resp.json()["teams"] if t["name"] == USER_TEAM)
    assert user_team["captain"] == roster_names[0]
    assert user_team["vice_captain"] == roster_names[1]


async def test_set_leadership_invalid(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)

    resp = await client.post(
        f"/careers/{career['id']}/leadership",
        json={"captain": "Not A Player", "vice": "Also Not A Player"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


async def test_set_presets(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    career_id = career["id"]

    resp = await client.get(f"/careers/{career_id}/payload", headers=auth_headers)
    user_team = next(t for t in resp.json()["teams"] if t["name"] == USER_TEAM)
    batting_order = [p["name"] for p in user_team["roster"][:11]]

    resp = await client.post(
        f"/careers/{career_id}/presets",
        json={"batting_order": batting_order},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    user_team = next(t for t in resp.json()["teams"] if t["name"] == USER_TEAM)
    assert user_team["saved_batting_order"] == batting_order


async def test_simulate_round_advances_season(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    career_id = career["id"]

    resp = await client.post(f"/careers/{career_id}/season/simulate-round", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["round"] == 2
    assert len(payload["fixture_results"]) >= 5


async def test_season_action_blocked_during_live_match(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    career_id = career["id"]

    resp = await client.post(f"/careers/{career_id}/match/begin", headers=auth_headers)
    assert resp.status_code == 200, resp.text

    resp = await client.post(
        f"/careers/{career_id}/leadership", json={"captain": "X", "vice": "Y"}, headers=auth_headers
    )
    assert resp.status_code == 400


async def test_full_season_to_retention_cycle(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    career_id = career["id"]

    # Run all 14 league rounds.
    for _ in range(14):
        resp = await client.post(f"/careers/{career_id}/season/simulate-round", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        payload = resp.json()

    assert payload["phase"] == "league_complete"

    resp = await client.post(f"/careers/{career_id}/season/start-playoffs", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["phase"] == "playoffs"

    # Run the 4 playoff matches.
    for _ in range(4):
        resp = await client.post(f"/careers/{career_id}/season/simulate-round", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        payload = resp.json()

    assert payload["phase"] == "season_end"
    assert len(payload["history"]) == 1

    resp = await client.post(f"/careers/{career_id}/retention/open", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["phase"] == "retention"
    retention_limit = payload["retention_limit"]

    user_team = next(t for t in payload["teams"] if t["name"] == USER_TEAM)
    keep_names = [p["name"] for p in user_team["roster"][:retention_limit]]

    resp = await client.post(
        f"/careers/{career_id}/retention", json={"players": keep_names}, headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["phase"] == "draft"
    assert payload["season"] == 2027


async def test_retention_wrong_count_rejected(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    career_id = career["id"]

    for _ in range(14):
        await client.post(f"/careers/{career_id}/season/simulate-round", headers=auth_headers)
    await client.post(f"/careers/{career_id}/season/start-playoffs", headers=auth_headers)
    for _ in range(4):
        await client.post(f"/careers/{career_id}/season/simulate-round", headers=auth_headers)
    await client.post(f"/careers/{career_id}/retention/open", headers=auth_headers)

    resp = await client.post(
        f"/careers/{career_id}/retention", json={"players": ["Only One Player"]}, headers=auth_headers
    )
    assert resp.status_code == 400


async def test_retention_open_requires_season_end(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)

    resp = await client.post(f"/careers/{career['id']}/retention/open", headers=auth_headers)
    assert resp.status_code == 400


async def test_start_playoffs_requires_league_complete(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)

    resp = await client.post(f"/careers/{career['id']}/season/start-playoffs", headers=auth_headers)
    assert resp.status_code == 400
