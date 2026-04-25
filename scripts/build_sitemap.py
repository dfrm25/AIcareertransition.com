#!/usr/bin/env python3
"""Regenerate sitemap.xml from all HTML files under repo root. Run before deploy."""
from __future__ import annotations

import datetime
import xml.etree.ElementTree as ET
from pathlib import Path

_UTC = getattr(datetime, "UTC", datetime.timezone.utc)

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://aicareertransition.com"

# Priority hints by path prefix / name
def priority_for(rel_posix: str) -> str:
    if rel_posix == "index.html":
        return "1.0"
    if rel_posix == "prompts.html":
        return "0.95"
    if rel_posix in ("101.html", "201.html"):
        return "0.9"
    if rel_posix.startswith("personas/"):
        return "0.82"
    if rel_posix == "career.html":
        return "0.88"
    if rel_posix == "blog.html":
        return "0.8"
    if rel_posix.startswith("blog/"):
        return "0.72"
    return "0.65"


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

    for p in html_files:
        rel = p.relative_to(ROOT).as_posix()
        url_el = ET.SubElement(urlset, "url")
        ET.SubElement(url_el, "loc").text = loc_for(rel)
        mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime, tz=_UTC).strftime("%Y-%m-%d")
        ET.SubElement(url_el, "lastmod").text = mtime
        ET.SubElement(url_el, "changefreq").text = "monthly" if "blog" not in rel else "monthly"
        ET.SubElement(url_el, "priority").text = priority_for(rel)

    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ")
    out = ROOT / "sitemap.xml"
    tree.write(out, encoding="UTF-8", xml_declaration=True)
    print(f"Wrote {out} with {len(html_files)} URLs (generator date {today})")


if __name__ == "__main__":
    main()
