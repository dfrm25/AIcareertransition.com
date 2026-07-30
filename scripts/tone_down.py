#!/usr/bin/env python3
"""Site-wide palette sweep: remove neon accent bars and inline color overrides.

Elegant, uniform look:
  1. Strip colored `border-left: Npx solid <color>` accent bars from cards.
  2. Remove inline background/color/border-color overrides on .prompt-card-category
     chips so they inherit the calm muted badge defined in styles.css.
  3. Normalize colored pill links (border-radius:20px) to a single subtle blue.

Idempotent. Run: python3 scripts/tone_down.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BORDER_LEFT_RE = re.compile(r'\s*border-left:\s*\d+px\s+solid\s+[^;"]+;?')
CHIP_RE = re.compile(r'(class="prompt-card-category"\s+style=")([^"]*)(")')
PILL_STYLE_RE = re.compile(r'style="([^"]*border-radius:\s*20px[^"]*)"')


def clean_chip(m: re.Match) -> str:
    pre, style, post = m.group(1), m.group(2), m.group(3)
    style = re.sub(r'border-color:[^;"]*;?', "", style)
    style = re.sub(r'background:[^;"]*;?', "", style)
    style = re.sub(r'color:[^;"]*;?', "", style)
    style = re.sub(r"\s{2,}", " ", style).strip()
    return f"{pre}{style}{post}"


def clean_pill(m: re.Match) -> str:
    style = m.group(1)
    style = re.sub(r"background:\s*rgba\([^)]*\)", "background:rgba(37,99,235,0.08)", style)
    style = re.sub(r"color:\s*#[0-9a-fA-F]{3,6}", "color:var(--color-accent-primary)", style)
    return f'style="{style}"'


def process(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    orig = text

    n_border = len(BORDER_LEFT_RE.findall(text))
    text = BORDER_LEFT_RE.sub("", text)

    n_chip = len(CHIP_RE.findall(text))
    text = CHIP_RE.sub(clean_chip, text)

    n_pill = len(PILL_STYLE_RE.findall(text))
    text = PILL_STYLE_RE.sub(clean_pill, text)

    if text != orig:
        path.write_text(text, encoding="utf-8")
    return {"border": n_border, "chip": n_chip, "pill": n_pill, "changed": text != orig}


def main() -> None:
    totals = {"border": 0, "chip": 0, "pill": 0, "files": 0}
    for p in sorted(ROOT.rglob("*.html")):
        if any(part.startswith(".") for part in p.parts):
            continue
        r = process(p)
        if r["changed"]:
            totals["files"] += 1
            totals["border"] += r["border"]
            totals["chip"] += r["chip"]
            totals["pill"] += r["pill"]
            print(f"  {p.relative_to(ROOT)}: borders={r['border']} chips={r['chip']} pills={r['pill']}")
    print(
        f"Done. {totals['files']} files changed · "
        f"{totals['border']} accent bars removed · {totals['chip']} chips neutralized · "
        f"{totals['pill']} pills normalized."
    )


if __name__ == "__main__":
    main()
