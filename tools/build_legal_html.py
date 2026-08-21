#!/usr/bin/env python3
"""Render docs/legal/*.md into the .html pages GitHub Pages publishes.

GitHub Pages serves docs/ from main as-is (a "legacy" build, no Jekyll step we
control), so the .html files have to be committed. They were previously
maintained by hand alongside the .md, which meant every edit had to be made
twice -- and one that was made only once produced a published privacy policy
describing the wrong app.

Markdown here is a small, fixed dialect: h1-h3, `- ` lists (one level of
nesting), `> ` blockquotes, `---` rules, `**bold**`, and bare emails. There is
no dependency on a Markdown library on purpose: the input is two files we
control, and a vendored 100-line renderer is easier to reason about in CI than
a third-party parser.

    python3 tools/build_legal_html.py           # write the .html files
    python3 tools/build_legal_html.py --check   # fail if they are out of date
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

LEGAL = Path(__file__).resolve().parent.parent / "docs" / "legal"

# (markdown source, published html, <title>). The title is not derived from the
# heading: the pages have used an ampersand and a site suffix since launch, and
# changing published titles is not this script's business.
PAGES = [
    ("privacy-policy.md", "privacy-policy.html", "Privacy Policy — Cric Sim"),
    ("terms-and-conditions.md", "terms.html", "Terms &amp; Conditions — Cric Sim"),
]

STYLE = (
    "body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:760px;"
    "margin:40px auto;padding:0 20px;line-height:1.6;color:#1a2233}"
    "h1{font-size:28px}h2{margin-top:32px;font-size:20px}h3{font-size:16px}"
    "blockquote{border-left:3px solid #ccc;margin:0;padding:4px 16px;color:#555}"
    "a{color:#1f6feb}hr{border:none;border-top:1px solid #eee;margin:28px 0}"
    "@media(prefers-color-scheme:dark){body{background:#0b0f17;color:#eef1f6}"
    "blockquote{color:#aaa}}"
)

EMAIL = re.compile(r"(?<![\w.@-])([\w.+-]+@[\w-]+\.[\w.]+)(?![\w@-])")
BOLD = re.compile(r"\*\*(.+?)\*\*", re.S)
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def inline(text: str) -> str:
    """Escape, then apply the inline markup we support."""
    out = html.escape(text, quote=False)
    out = LINK.sub(lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>', out)
    out = BOLD.sub(r"<strong>\1</strong>", out)
    # Emails are written bare in the Markdown but must be clickable on the page.
    out = EMAIL.sub(lambda m: f'<a href="mailto:{m.group(1)}">{m.group(1)}</a>', out)
    return out


def render(md: str) -> tuple[str, list[str]]:
    """Return (h1 text, body lines) for the markdown source."""
    title = ""
    body: list[str] = []
    # Depth of open <ul>s. A nested list lives inside the currently open <li>,
    # so that <li> stays unclosed until the nested list ends.
    depth = 0
    para: list[str] = []

    def flush_para() -> None:
        if para:
            body.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()

    def close_lists(to: int = 0) -> None:
        nonlocal depth
        while depth > to:
            body.append("</ul>" if depth == 1 else "</ul></li>")
            depth -= 1

    for raw in md.splitlines():
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_para()
            continue

        heading = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading:
            flush_para()
            close_lists()
            level, text = len(heading.group(1)), heading.group(2)
            if level == 1:
                title = inline(text)
            else:
                body.append(f"<h{level}>{inline(text)}</h{level}>")
            continue

        if stripped == "---":
            flush_para()
            close_lists()
            body.append("<hr>")
            continue

        if stripped.startswith("> "):
            flush_para()
            close_lists()
            body.append(f"<blockquote><p>{inline(stripped[2:])}</p></blockquote>")
            continue

        bullet = re.match(r"^(\s*)-\s+(.*)$", line)
        if bullet:
            flush_para()
            want = 1 if len(bullet.group(1)) < 2 else 2
            if want > depth:
                # Open the nested list *inside* the open <li>, so drop its close.
                if depth >= 1 and body and body[-1].endswith("</li>"):
                    body[-1] = body[-1][: -len("</li>")]
                body.append("<ul>")
                depth += 1
            else:
                close_lists(want)
            body.append(f"<li>{inline(bullet.group(2))}</li>")
            continue

        # An indented non-bullet line continues the list item above it.
        if depth and line.startswith("  "):
            close_lists(1)
            if body and body[-1].endswith("</li>"):
                body[-1] = body[-1][: -len("</li>")] + f"<p>{inline(stripped)}</p></li>"
                continue

        # A non-indented line after a list ends it. Without this the paragraph
        # is emitted inside the <ul>, which is invalid.
        if depth and not line.startswith("  "):
            close_lists()
        para.append(stripped)

    flush_para()
    close_lists()
    return title, body


def build(md_name: str, title: str) -> str:
    h1, body = render((LEGAL / md_name).read_text())
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f"<title>{title}</title>\n"
        f"<style>{STYLE}</style>\n"
        f"</head><body><h1>{h1}</h1>\n" + "\n".join(body) + "</body></html>"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="fail if the .html is stale")
    args = ap.parse_args()

    stale: list[str] = []
    for md_name, html_name, title in PAGES:
        rendered = build(md_name, title)
        target = LEGAL / html_name
        current = target.read_text() if target.exists() else None
        if current == rendered:
            continue
        if args.check:
            stale.append(html_name)
        else:
            target.write_text(rendered)
            print(f"wrote {html_name}")

    if stale:
        print("Generated legal pages are out of date:\n")
        for name in stale:
            print(f"  - docs/legal/{name}")
        print("\nRun: make legal")
        return 1

    print("Legal pages up to date." if args.check else "Legal pages built.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
