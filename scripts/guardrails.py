#!/usr/bin/env python3
"""Automated quality gate for the site — the safety net for unattended deploys.

Runs a series of checks and exits non-zero if any HARD check fails, which the
weekly workflow uses to BLOCK deployment. Because no human reviews the weekly
content, this is what keeps stale/broken content off the live site.

Checks:
  1. Deprecated-model / stale-name scan (hard fail)
  2. Valid XML for sitemap.xml and feed.xml (hard fail)
  3. Internal link integrity — local .html hrefs resolve to real files (hard fail)
  4. This-week hub still has its update markers (hard fail)
  5. Every page has <title> and meta description (soft warn)

Usage: python3 scripts/guardrails.py
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Clearly deprecated / retired names that should never appear in live copy.
# Kept conservative on purpose: only names that are unambiguously stale.
DEPRECATED_PATTERNS = [
    r"gemini\s*2\.0\s*flash",
    r"gemini\s*1\.5",
    r"gemini\s*1\.0",
    r"\bgpt-3\.5\b",
    r"\bgpt-3\b",
    r"text-davinci",
    r"\bclaude\s*2\b",
    r"\bclaude\s*instant\b",
    r"\bgoogle\s+bard\b",
    r"\bbard\b(?!\w)",
    r"\bo1-preview\b",
    r"\bgpt-4\.0\b",
]

# Official domains allowed as primary sources in weekly content.
OFFICIAL_DOMAINS = (
    "openai.com",
    "anthropic.com",
    "claude.com",
    "google.com",
    "blog.google",
    "ai.google.dev",
    "cloud.google.com",
    "deepmind.google",
    "microsoft.com",
)

HREF_RE = re.compile(r'href="([^"#?]+\.html)(?:[#?][^"]*)?"')
TITLE_RE = re.compile(r"<title>.*?</title>", re.DOTALL | re.IGNORECASE)
DESC_RE = re.compile(r'<meta[^>]*name="description"', re.IGNORECASE)

errors: list[str] = []
warnings: list[str] = []


def html_files() -> list[Path]:
    out = []
    for p in ROOT.rglob("*.html"):
        if any(part.startswith(".") for part in p.parts):
            continue
        out.append(p)
    return out


def check_deprecated(files: list[Path]) -> None:
    combined = [re.compile(p, re.IGNORECASE) for p in DEPRECATED_PATTERNS]
    for p in files:
        text = p.read_text(encoding="utf-8", errors="ignore")
        for rx in combined:
            m = rx.search(text)
            if m:
                errors.append(
                    f"[deprecated-name] {p.relative_to(ROOT)} contains '{m.group(0)}'"
                )


def check_xml() -> None:
    for name in ("sitemap.xml", "feed.xml"):
        path = ROOT / name
        if not path.exists():
            errors.append(f"[xml] {name} is missing")
            continue
        try:
            ET.parse(path)
        except ET.ParseError as e:
            errors.append(f"[xml] {name} is invalid: {e}")


def check_internal_links(files: list[Path]) -> None:
    for p in files:
        text = p.read_text(encoding="utf-8", errors="ignore")
        for href in HREF_RE.findall(text):
            if href.startswith(("http://", "https://", "//", "mailto:", "tel:")):
                continue
            target = (p.parent / href).resolve()
            if not target.exists():
                errors.append(
                    f"[dead-link] {p.relative_to(ROOT)} -> '{href}' (missing)"
                )


def check_hub_markers() -> None:
    hub = ROOT / "this-week.html"
    if not hub.exists():
        errors.append("[hub] this-week.html is missing")
        return
    text = hub.read_text(encoding="utf-8", errors="ignore")
    for marker in (
        "<!-- WEEKLY:DATE -->",
        "<!-- WEEKLY:UPDATES:START -->",
        "<!-- WEEKLY:UPDATES:END -->",
        "<!-- WEEKLY:TRACKER:START -->",
        "<!-- WEEKLY:PROMPT:START -->",
    ):
        if marker not in text:
            errors.append(f"[hub] missing marker {marker} in this-week.html")
    if re.search(r'<time id="hub-updated"[^>]*\bhidden\b', text):
        errors.append("[hub] last-reviewed date on this-week.html is hidden")
    if not re.search(r'<time id="hub-updated" datetime="\d{4}-\d{2}-\d{2}"', text):
        errors.append("[hub] this-week.html is missing a dated hub-updated time")


def check_meta(files: list[Path]) -> None:
    for p in files:
        text = p.read_text(encoding="utf-8", errors="ignore")
        if not TITLE_RE.search(text):
            warnings.append(f"[meta] {p.relative_to(ROOT)} has no <title>")
        if not DESC_RE.search(text):
            warnings.append(f"[meta] {p.relative_to(ROOT)} has no meta description")


def main() -> int:
    files = html_files()
    check_deprecated(files)
    check_xml()
    check_internal_links(files)
    check_hub_markers()
    check_meta(files)

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  ! {w}")

    if errors:
        print(f"\nGUARDRAILS FAILED — {len(errors)} hard error(s). Deployment blocked:")
        for e in errors:
            print(f"  x {e}")
        return 1

    print(f"\nGUARDRAILS PASSED — {len(files)} pages checked, 0 hard errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
