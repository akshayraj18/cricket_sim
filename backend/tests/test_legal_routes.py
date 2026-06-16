"""The public legal pages (Terms of Service / Privacy Policy).

These back the in-app legal links and the App Store / Play Store policy URLs, so
they must be reachable without auth, return HTML, and contain the actual policy
content (not an empty shell).
"""
import pytest
from httpx import AsyncClient

from app.legal.content import APP_NAME, CONTACT_EMAIL


@pytest.mark.parametrize(
    "path, heading",
    [
        ("/legal/terms", "Terms of Service"),
        ("/legal/privacy", "Privacy Policy"),
    ],
)
async def test_legal_page_renders_html_without_auth(client: AsyncClient, path: str, heading: str):
    resp = await client.get(path)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    body = resp.text
    assert f"<h1>{heading}</h1>" in body
    assert APP_NAME in body
    # The contact email must be present so users (and store reviewers) can reach
    # us — App Store rejects policies without a working contact.
    assert CONTACT_EMAIL in body


async def test_legal_pages_have_substantive_content(client: AsyncClient):
    """Guard against the template rendering with empty section bodies."""
    for path in ("/legal/terms", "/legal/privacy"):
        body = (await client.get(path)).text
        # Several numbered sections, each with paragraph copy.
        assert body.count("<h2>") >= 5
        assert body.count("<p>") >= 5
