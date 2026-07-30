#!/usr/bin/env python3
"""One-time wiring: add the 'This Week' nav link and an RSS <link> to every page.

Idempotent — safe to re-run. Inserts a nav link right after the Home link and a
single RSS alternate link before </head>. Skips files that already have them.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HOME_RE = re.compile(
    r'(<a href="(?:\.\./)?index\.html" class="navbar-link[^"]*">Home</a>)'
)
RSS_LINK = (
    '<link rel="alternate" type="application/rss+xml" '
    'title="AI Career Transition — This Week in AI" href="/feed.xml">'
)


def process(path: Path) -> tuple[bool, bool]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    orig = text
    prefix = "../" if path.parent != ROOT else ""

    nav_added = False
    if 'this-week.html" class="navbar-link' not in text:
        link = f'<a href="{prefix}this-week.html" class="navbar-link">This Week</a>'
        m = HOME_RE.search(text)
        if m:
            insert_at = m.end()
            # Preserve any whitespace/newline formatting that follows the Home link.
            ws = re.match(r"\s*", text[insert_at:]).group(0)
            text = text[:insert_at] + ws + link + text[insert_at + len(ws):]
            nav_added = True

    rss_added = False
    if "application/rss+xml" not in text and "</head>" in text:
        text = text.replace("</head>", f"  {RSS_LINK}\n</head>", 1)
        rss_added = True

    if text != orig:
        path.write_text(text, encoding="utf-8")
    return nav_added, rss_added


def main() -> None:
    nav_count = rss_count = 0
    for p in sorted(ROOT.rglob("*.html")):
        if any(part.startswith(".") for part in p.parts):
            continue
        if p.name == "this-week.html":
            continue
        nav, rss = process(p)
        nav_count += nav
        rss_count += rss
        if nav or rss:
            print(f"  {p.relative_to(ROOT)}: nav={nav} rss={rss}")
    print(f"Done. Added nav link to {nav_count} files, RSS link to {rss_count} files.")


if __name__ == "__main__":
    main()
