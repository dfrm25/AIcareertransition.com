#!/usr/bin/env python3
"""Regenerate feed.xml (RSS 2.0) from blog posts and the weekly hub.

Reads each blog/*.html file, extracts its JSON-LD BlogPosting (headline,
description, datePublished) plus the canonical URL, sorts newest-first, and
writes a valid RSS 2.0 feed. Machine-readable freshness signal for AI
aggregators, RSS readers, and search engines. Run before deploy.
"""
from __future__ import annotations

import datetime
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://aicareertransition.com"
FEED_TITLE = "AI Career Transition — This Week in AI"
FEED_DESC = (
    "Weekly AI model, agent, and workflow updates plus new career guides for "
    "professionals. Official-source-first, no hype."
)

_UTC = getattr(datetime, "UTC", datetime.timezone.utc)
_LD_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)
_CANON_RE = re.compile(
    r'<link[^>]*rel="canonical"[^>]*href="([^"]+)"', re.IGNORECASE
)
_DESC_RE = re.compile(
    r'<meta[^>]*name="description"[^>]*content="([^"]*)"', re.IGNORECASE
)
_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL | re.IGNORECASE)


def _iter_ld(text: str):
    for block in _LD_RE.findall(text):
        try:
            data = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            for item in data:
                yield item
        else:
            yield data


def _post_type(item: dict) -> bool:
    t = item.get("@type", "")
    if isinstance(t, list):
        return any(x in ("BlogPosting", "Article", "NewsArticle") for x in t)
    return t in ("BlogPosting", "Article", "NewsArticle")


def extract_post(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if re.search(r'<meta[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*noindex', text[:8000], re.I):
        return None
    posting = next((i for i in _iter_ld(text) if isinstance(i, dict) and _post_type(i)), None)

    canon = _CANON_RE.search(text)
    url = canon.group(1) if canon else f"{BASE}/blog/{path.name}"

    if posting:
        headline = posting.get("headline") or ""
        desc = posting.get("description") or ""
        date = posting.get("datePublished") or posting.get("dateModified") or ""
        if isinstance(posting.get("mainEntityOfPage"), dict):
            url = posting["mainEntityOfPage"].get("@id", url)
        elif isinstance(posting.get("url"), str):
            url = posting["url"]
    else:
        m = _TITLE_RE.search(text)
        headline = (m.group(1).split("|")[0].strip() if m else path.stem)
        d = _DESC_RE.search(text)
        desc = d.group(1) if d else ""
        date = ""

    if not date:
        return None

    try:
        dt = datetime.datetime.strptime(date[:10], "%Y-%m-%d").replace(tzinfo=_UTC)
    except ValueError:
        return None

    return {
        "title": html.unescape(headline).strip(),
        "description": html.unescape(desc).strip(),
        "url": url,
        "date": dt,
    }


def rfc822(dt: datetime.datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


def main() -> None:
    blog_dir = ROOT / "blog"
    posts: list[dict] = []
    for p in sorted(blog_dir.glob("*.html")):
        item = extract_post(p)
        if item and item["title"]:
            posts.append(item)

    posts.sort(key=lambda x: x["date"], reverse=True)

    now = datetime.datetime.now(_UTC)
    latest = posts[0]["date"] if posts else now

    items_xml = []
    for post in posts:
        items_xml.append(
            "    <item>\n"
            f"      <title>{html.escape(post['title'])}</title>\n"
            f"      <link>{html.escape(post['url'])}</link>\n"
            f"      <guid isPermaLink=\"true\">{html.escape(post['url'])}</guid>\n"
            f"      <pubDate>{rfc822(post['date'])}</pubDate>\n"
            f"      <description>{html.escape(post['description'])}</description>\n"
            "    </item>"
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        f"    <title>{html.escape(FEED_TITLE)}</title>\n"
        f"    <link>{BASE}/this-week.html</link>\n"
        f'    <atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml" />\n'
        f"    <description>{html.escape(FEED_DESC)}</description>\n"
        "    <language>en-us</language>\n"
        f"    <lastBuildDate>{rfc822(latest)}</lastBuildDate>\n"
        f"    <pubDate>{rfc822(latest)}</pubDate>\n"
        "    <ttl>1440</ttl>\n"
        + "\n".join(items_xml)
        + "\n  </channel>\n</rss>\n"
    )

    out = ROOT / "feed.xml"
    out.write_text(xml, encoding="utf-8")
    print(f"Wrote {out} with {len(posts)} items (newest {latest:%Y-%m-%d})")


if __name__ == "__main__":
    main()
