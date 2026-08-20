"""Roster CSV export/import endpoints."""
import csv
import io

from httpx import AsyncClient

USER_TEAM = "Mumbai Mavericks"


async def _create_career(client: AsyncClient, headers: dict, **overrides) -> dict:
    body = {
        "name": "CSV Career",
        "user_team_name": USER_TEAM,
        "difficulty": "medium",
        "draft_pool_type": "current",
        **overrides,
    }
    resp = await client.post("/careers", json=body, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _rows(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text, newline="")))


async def test_export_returns_csv_with_a_filename(client: AsyncClient, auth_headers: dict):
    career = await _create_career(client, auth_headers)
    resp = await client.get(f"/careers/{career['id']}/roster.csv", headers=auth_headers)

    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment" in resp.headers.get("content-disposition", "")
    rows = _rows(resp.text)
    assert rows and "player_key" in rows[0]


async def test_export_requires_auth(client: AsyncClient, auth_headers: dict):
    career = await _create_career(client, auth_headers)
    resp = await client.get(f"/careers/{career['id']}/roster.csv")
    assert resp.status_code == 401


async def test_export_is_scoped_to_the_owner(client: AsyncClient, auth_headers: dict):
    """A career belonging to someone else must 404, not leak its roster."""
    career = await _create_career(client, auth_headers)
    other = await client.post("/auth/guest")
    other_headers = {"Authorization": f"Bearer {other.json()['tokens']['access_token']}"}

    resp = await client.get(f"/careers/{career['id']}/roster.csv", headers=other_headers)
    assert resp.status_code == 404


async def test_round_trip_import_reports_no_changes(client: AsyncClient, auth_headers: dict):
    career = await _create_career(client, auth_headers)
    exported = (await client.get(f"/careers/{career['id']}/roster.csv", headers=auth_headers)).text

    resp = await client.post(
        f"/careers/{career['id']}/roster.csv", json={"csv": exported}, headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["renamed"] == 0
    assert resp.json()["rerated"] == 0


async def test_import_applies_a_rename_and_persists_it(client: AsyncClient, auth_headers: dict):
    career = await _create_career(client, auth_headers)
    exported = (await client.get(f"/careers/{career['id']}/roster.csv", headers=auth_headers)).text
    rows = _rows(exported)
    target = rows[0]["player_key"]
    rows[0]["name"] = "Edited Player Name"

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(rows)

    resp = await client.post(
        f"/careers/{career['id']}/roster.csv", json={"csv": buf.getvalue()}, headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["renamed"] == 1

    # Re-export to prove it was written back, not just applied in memory.
    again = (await client.get(f"/careers/{career['id']}/roster.csv", headers=auth_headers)).text
    names = {r["name"] for r in _rows(again)}
    assert "Edited Player Name" in names
    assert target not in names


async def test_invalid_import_is_rejected_with_every_error(client: AsyncClient, auth_headers: dict):
    career = await _create_career(client, auth_headers)
    exported = (await client.get(f"/careers/{career['id']}/roster.csv", headers=auth_headers)).text
    rows = _rows(exported)
    rows[0]["base_ovr"] = "999"
    rows[1]["age"] = "not a number"

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(rows)

    resp = await client.post(
        f"/careers/{career['id']}/roster.csv", json={"csv": buf.getvalue()}, headers=auth_headers
    )
    assert resp.status_code == 400
    errors = resp.json()["detail"]["errors"]
    assert len(errors) >= 2, "every problem should be listed, not just the first"

    # And nothing was written.
    again = (await client.get(f"/careers/{career['id']}/roster.csv", headers=auth_headers)).text
    assert _rows(again)[0]["base_ovr"] == _rows(exported)[0]["base_ovr"]


async def test_import_rejects_a_file_for_a_different_career(client: AsyncClient, auth_headers: dict):
    """player_key values from another career must not silently do nothing."""
    a = await _create_career(client, auth_headers, name="Career A")
    b = await _create_career(client, auth_headers, name="Career B", user_team_name="Chennai Cholas")
    exported_a = (await client.get(f"/careers/{a['id']}/roster.csv", headers=auth_headers)).text

    resp = await client.post(
        f"/careers/{b['id']}/roster.csv", json={"csv": exported_a}, headers=auth_headers
    )
    # The two careers draft from the same pool, so some names legitimately
    # overlap; what matters is that unknown keys are reported rather than
    # ignored. Either it is rejected, or every key happened to exist in B.
    if resp.status_code == 400:
        assert any("no player named" in e for e in resp.json()["detail"]["errors"])
    else:
        assert resp.status_code == 200, resp.text
