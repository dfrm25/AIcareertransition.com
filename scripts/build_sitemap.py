#!/usr/bin/env python3
"""Regenerate sitemap.xml from all HTML files under repo root. Run before deploy."""
from __future__ import annotations

import datetime
import re
import xml.etree.ElementTree as ET
from pathlib import Path

_UTC = getattr(datetime, "UTC", datetime.timezone.utc)

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://aicareertransition.com"

# Priority hints by path prefix / name
def priority_for(rel_posix: str) -> str:
    if rel_posix == "index.html":
        return "1.0"
    if rel_posix in ("prompts.html", "this-week.html"):
        return "0.95"
    if rel_posix in ("101.html", "201.html"):
        return "0.9"
    if rel_posix.startswith("guides/"):
        return "0.9"
    if rel_posix.startswith("research/"):
        return "0.86"
    if rel_posix.startswith("personas/"):
        return "0.82"
    if rel_posix in ("career.html", "use-cases.html"):
        return "0.88"
    if rel_posix == "blog.html":
        return "0.8"
    if rel_posix.startswith("blog/"):
        return "0.72"
    return "0.65"


def changefreq_for(rel_posix: str) -> str:
    if rel_posix in ("index.html", "this-week.html", "blog.html"):
        return "weekly"
    if rel_posix.startswith("blog/weekly-ai-brief-"):
        return "weekly"
    return "monthly"


NOINDEX_RE = re.compile(
    r'<meta[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*noindex',
    re.IGNORECASE,
)


def is_noindex(path: Path) -> bool:
    head = path.read_text(encoding="utf-8", errors="ignore")[:8000]
    return bool(NOINDEX_RE.search(head))


# Content that changed on 2026-09-27. Nav-only edits keep the prior sitemap date
# (2026-09-21) so lastmod is not stamped on every URL.
CHANGED_ON_2026_09_27 = {
    "index.html",
    "this-week.html",
    "career.html",
    "101.html",
    "201.html",
    "prompts.html",
    "use-cases.html",
    "artifacts.html",
    "guides/product-manager-ai-transition.html",
    "personas/marketing.html",
    "personas/analytics.html",
    "personas/product.html",
    "personas/copywriting.html",
    "personas/data-science.html",
    "blog/ai-lab-updates-career-actions-apr-2026.html",
    "blog/ai-career-transition-salary-outlook.html",
    "blog/ai-career-transition-no-code.html",
    "blog/ai-skills-resume-without-sounding-fake.html",
    "blog/ai-career-transition-timeline.html",
    "blog/ai-career-transition-portfolio-examples.html",
    "blog/ai-career-transition-roadmap.html",
    "blog/ai-career-transition-interview-prep.html",
    "blog/chrome-mobile-ai-mode-any-website.html",
    "blog/copilot-better-model-than-auto.html",
    "blog/copilot-work-iq-on-off.html",
}
PRIOR_LASTMOD = "2026-09-21"


def lastmod_for(rel_posix: str) -> str:
    if rel_posix in CHANGED_ON_2026_09_27:
        return "2026-09-27"
    return PRIOR_LASTMOD


def loc_for(rel_posix: str) -> str:
    if rel_posix == "index.html":
        return f"{BASE}/"
    if rel_posix.endswith("/index.html"):
        return f"{BASE}/{rel_posix[:-10].rstrip('/')}/"
    return f"{BASE}/{rel_posix}"


def main() -> None:
    html_files: list[Path] = []
    for p in ROOT.rglob("*.html"):
        if any(part.startswith(".") for part in p.parts):
            continue
        html_files.append(p)

    html_files.sort(key=lambda x: x.relative_to(ROOT).as_posix())

    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    today = datetime.datetime.now(_UTC).strftime("%Y-%m-%d")

    included = 0
    for p in html_files:
        if is_noindex(p):
            continue
        rel = p.relative_to(ROOT).as_posix()
        loc = loc_for(rel)
        if loc.endswith("/index.html") or loc.endswith("index.html"):
            raise SystemExit(f"sitemap loc must not include index.html: {loc}")
        url_el = ET.SubElement(urlset, "url")
        ET.SubElement(url_el, "loc").text = loc
        ET.SubElement(url_el, "lastmod").text = lastmod_for(rel)
        ET.SubElement(url_el, "changefreq").text = changefreq_for(rel)
        ET.SubElement(url_el, "priority").text = priority_for(rel)
        included += 1

    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ")
    out = ROOT / "sitemap.xml"
    tree.write(out, encoding="UTF-8", xml_declaration=True)
    print(f"Wrote {out} with {included} URLs (skipped {len(html_files) - included} noindex; generator date {today})")


if __name__ == "__main__":
    main()
