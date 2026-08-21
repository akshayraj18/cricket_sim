#!/usr/bin/env python3
"""Check that each legal document's .html mirror matches its .md source.

The App links users to the .html files, but the .md files are what anyone
actually reads when editing. They are maintained by hand, so nothing stops a
change landing in one and not the other -- and a privacy policy that describes
the wrong app is the kind of bug you only find when it matters.

This is deliberately shallow: it compares the "Last updated" date and the set
of headings, which is enough to catch a section added, removed, renamed, or a
date bumped on one side only. It does not diff prose.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

LEGAL = Path(__file__).resolve().parent.parent / "docs" / "legal"

# (markdown source, published html)
PAIRS = [
    ("privacy-policy.md", "privacy-policy.html"),
    ("terms-and-conditions.md", "terms.html"),
]

# Case-insensitive: _norm() lowercases before this runs.
DATE = re.compile(r"last updated:\s*([a-z]+ \d{1,2}, \d{4})", re.I)


def _norm(text: str) -> str:
    """Strip markup and whitespace so the two formats compare like for like."""
    text = re.sub(r"<[^>]+>", "", text)          # html tags
    text = re.sub(r"[*_`]", "", text)            # markdown emphasis
    return re.sub(r"\s+", " ", html.unescape(text)).strip().lower()


def md_headings(src: str) -> list[str]:
    return [_norm(m.group(2)) for m in re.finditer(r"^(#{2,3})\s+(.*)$", src, re.M)]


def html_headings(src: str) -> list[str]:
    return [_norm(m.group(1)) for m in re.finditer(r"<h[23]>(.*?)</h[23]>", src, re.S)]


def date_of(src: str, label: str, problems: list[str]) -> str | None:
    found = DATE.search(_norm(src))
    if not found:
        problems.append(f"{label}: no 'Last updated: <Month D, YYYY>' line")
        return None
    # _norm lowercases, so compare case-insensitively downstream.
    return found.group(1)


def main() -> int:
    problems: list[str] = []
    for md_name, html_name in PAIRS:
        md_path, html_path = LEGAL / md_name, LEGAL / html_name
        for path in (md_path, html_path):
            if not path.exists():
                problems.append(f"missing file: {path}")
        if problems:
            break

        md_src, html_src = md_path.read_text(), html_path.read_text()

        md_date = date_of(md_src, md_name, problems)
        html_date = date_of(html_src, html_name, problems)
        if md_date and html_date and md_date != html_date:
            problems.append(
                f"{md_name} says '{md_date}' but {html_name} says '{html_date}' "
                f"-- one was updated without the other"
            )

        md_h, html_h = md_headings(md_src), html_headings(html_src)
        only_md = [h for h in md_h if h not in html_h]
        only_html = [h for h in html_h if h not in md_h]
        for h in only_md:
            problems.append(f"heading in {md_name} but not {html_name}: {h!r}")
        for h in only_html:
            problems.append(f"heading in {html_name} but not {md_name}: {h!r}")

    if problems:
        print("Legal docs are out of sync:\n")
        for p in problems:
            print(f"  - {p}")
        print(f"\n{len(problems)} problem(s). Update both the .md and the .html.")
        return 1

    print(f"Legal docs in sync ({len(PAIRS)} pairs checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
