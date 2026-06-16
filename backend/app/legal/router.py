"""Public legal pages: Terms of Service and Privacy Policy.

Served as standalone, mobile-friendly HTML (no auth) so they double as the
public policy URLs required by the App Store / Play Store and as the targets of
the in-app "Terms of Service" / "Privacy Policy" links. Content lives in
`content.py`; this module is just presentation.
"""
import html

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.legal.content import (
    APP_NAME,
    LAST_UPDATED,
    PRIVACY_SECTIONS,
    TERMS_SECTIONS,
)

router = APIRouter(prefix="/legal", tags=["legal"])

# Minimal, self-contained styling — dark theme matching the app, readable on
# phones, no external assets so the page renders offline-cached and crawlable.
_PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="dark light">
<title>{title} · {app_name}</title>
<style>
  :root {{ color-scheme: dark light; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: #0b1220;
    color: #e6eaf2;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.6;
  }}
  .wrap {{ max-width: 720px; margin: 0 auto; padding: 32px 20px 64px; }}
  .eyebrow {{
    text-transform: uppercase; letter-spacing: 1.5px; font-size: 12px;
    font-weight: 800; color: #8e9bb3; margin: 0 0 8px;
  }}
  h1 {{ font-size: 28px; line-height: 1.2; margin: 0 0 4px; }}
  .updated {{ color: #8e9bb3; font-size: 13px; margin: 0 0 32px; }}
  h2 {{ font-size: 18px; margin: 28px 0 8px; color: #f0b429; }}
  p {{ margin: 0 0 12px; color: #c4ccda; }}
  a {{ color: #3ddc84; }}
  footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #1e2738; color: #5d6b85; font-size: 13px; }}
</style>
</head>
<body>
  <main class="wrap">
    <p class="eyebrow">{app_name}</p>
    <h1>{title}</h1>
    <p class="updated">Last updated: {last_updated}</p>
    {body}
    <footer>© {year} {app_name}. All rights reserved.</footer>
  </main>
</body>
</html>"""


def _render(title: str, sections: list[tuple[str, list[str]]]) -> str:
    """Render policy sections into the page template, escaping all dynamic text."""
    parts: list[str] = []
    for heading, paragraphs in sections:
        parts.append(f"<h2>{html.escape(heading)}</h2>")
        for para in paragraphs:
            parts.append(f"<p>{html.escape(para)}</p>")
    return _PAGE_TEMPLATE.format(
        title=html.escape(title),
        app_name=html.escape(APP_NAME),
        last_updated=html.escape(LAST_UPDATED),
        body="\n    ".join(parts),
        year=LAST_UPDATED.rsplit(" ", 1)[-1],
    )


@router.get("/terms", response_class=HTMLResponse)
async def terms_of_service() -> str:
    return _render("Terms of Service", TERMS_SECTIONS)


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_policy() -> str:
    return _render("Privacy Policy", PRIVACY_SECTIONS)
