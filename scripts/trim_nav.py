#!/usr/bin/env python3
"""One-time: remove the 'Feedback' link from the top navbar on every page.

The nav had 10 items and was crowding into the Take Quiz button. Feedback is
still reachable from the footer and the on-page CTAs, so it is dropped from the
primary nav only. Idempotent.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAV_FEEDBACK_RE = re.compile(
    r'\s*<a href="(?:\.\./)?feedback\.html" class="navbar-link[^"]*">Feedback</a>'
)


def main() -> None:
    changed = 0
    for p in sorted(ROOT.rglob("*.html")):
        if any(part.startswith(".") for part in p.parts):
            continue
        text = p.read_text(encoding="utf-8")
        new = NAV_FEEDBACK_RE.sub("", text)
        if new != text:
            p.write_text(new, encoding="utf-8")
            changed += 1
            print(f"  {p.relative_to(ROOT)}")
    print(f"Done. Removed Feedback nav link from {changed} files.")


if __name__ == "__main__":
    main()
