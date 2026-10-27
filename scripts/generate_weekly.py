#!/usr/bin/env python3
"""Daily AI news refresh for This Week in AI. Runs unattended in GitHub Actions.

A Cursor agent reads official vendor pages and returns a JSON payload. This
script validates it and renders the hub, the home teaser, a dated brief, the
blog index, llms.txt, the feed, and the sitemap.

It publishes only when the agent finds at least MIN_UPDATES work-relevant
updates dated after the last published brief. On a quiet day it exits without
touching any file. There is no filler fallback: no agent, no change.

Env:
  CURSOR_API_KEY   required to publish (without it the run is a no-op)
  WEEKLY_MODEL     optional (default: composer-2.5)

Local test:
  python3 scripts/generate_weekly.py --payload payload.json --date 2026-10-30
"""
from __future__ import annotations

import datetime
import email.utils
import json
import os
import re
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_feed  # noqa: E402

_UTC = getattr(datetime, "UTC", datetime.timezone.utc)

OFFICIAL_DOMAINS = (
    "openai.com", "anthropic.com", "claude.com", "google.com", "blog.google",
    "googleblog.com", "ai.google.dev", "cloud.google.com", "deepmind.google",
    "microsoft.com",
)
DEPRECATED_RE = re.compile(
    r"gemini\s*2\.0\s*flash|gemini\s*1\.5|gemini\s*1\.0|\bgpt-3\.5\b|\bgpt-3\b|"
    r"text-davinci|\bclaude\s*2\b|\bclaude\s*instant\b|\bgoogle\s+bard\b|"
    r"\bbard\b(?!\w)|\bo1-preview\b|\bgpt-4\.0\b",
    re.IGNORECASE,
)
BANNED_RE = re.compile(
    r"\b(no hype|durable skills?|game[- ]changers?|unlock\w*|leverag\w*|seamless\w*|"
    r"delve\w*|cutting[- ]edge|supercharg\w*|in today's fast-paced|here is how|"
    r"the signal for professionals)\b",
    re.IGNORECASE,
)
EM_DASH_RE = re.compile(r"\u2014| -- ")
UNSAFE_TAG_RE = re.compile(r"<\s*(script|style|iframe|img|svg|form|input|object|embed)\b", re.I)
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CSS_VER = "20260928r2"
MIN_UPDATES = 3
MAX_UPDATES = 6
MIN_POST_WORDS = 600
VENDORS = ("OpenAI", "Anthropic", "Google", "Microsoft")

LEAD_FEEDS = (
    "https://openai.com/news/rss.xml",
    "https://blog.google/innovation-and-ai/rss/",
    "https://workspaceupdates.googleblog.com/feeds/posts/default",
    "https://www.microsoft.com/en-us/microsoft-365/blog/feed/",
    "https://www.microsoft.com/en-us/microsoft-copilot/blog/feed/",
)

INTERNAL_PAGES = (
    "101.html", "201.html", "prompts.html", "artifacts.html", "tools-comparison.html",
    "use-cases.html", "career.html",
    "blog/ai-workflow-evals-human-review.html",
    "blog/agentic-ai-workflows-for-non-engineers.html",
    "blog/mcp-and-connected-ai-tools-career-guide.html",
    "blog/ai-excel-analysis-mistakes.html",
    "blog/how-to-change-ai-model.html",
)


def _domain_ok(url: str) -> bool:
    return url.startswith("https://") and any(
        (f"//{d}" in url or f".{d}" in url) for d in OFFICIAL_DOMAINS
    )


def _norm_url(url: str) -> str:
    url = str(url or "").strip().split("#", 1)[0].split("?", 1)[0]
    if url.endswith("/"):
        url = url[:-1]
    return url.lower()


# Announcement URLs for GPT-6.1 Terra. A later daily run must not add a second card.
_TERRA_SOURCE_RE = re.compile(
    r"introducing-gpt-6-1-terra|gpt-6-1-terra-in-github-copilot|gpt-6-1-terra-now-generally-available",
    re.I,
)


def update_already_on_hub(update: dict, covered: list[str]) -> bool:
    """True when the hub already carries this announcement.

    Match ignores a trailing slash, query, or fragment. GPT-6.1 Terra also
    matches by its OpenAI, Microsoft, and GitHub announcement URLs, or by a
    title that names the model, once any of those URLs is already on the hub.
    """
    src = str(update.get("source_url") or "")
    norms = {_norm_url(item) for item in covered}
    if _norm_url(src) and _norm_url(src) in norms:
        return True
    if not any(_TERRA_SOURCE_RE.search(item) for item in covered):
        return False
    if _TERRA_SOURCE_RE.search(src):
        return True
    return re.search(r"gpt-6\.1\s*terra", str(update.get("title") or ""), re.I) is not None


# --------------------------------------------------------------------------- #
# 1. Leads from official feeds (hints for the agent, never published as-is)
# --------------------------------------------------------------------------- #
def _fetch(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": "AICareerTransitionNews/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as err:
        print(f"[warn] fetch failed {url}: {err}", file=sys.stderr)
        return None


def _parse_feed(xml_bytes: bytes) -> list[dict]:
    items = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return items
    for item in root.iter():
        tag = item.tag.lower().split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        title = link = ""
        published = None
        for child in item:
            ctag = child.tag.lower().split("}")[-1]
            text = (child.text or "").strip()
            if ctag == "title" and text:
                title = text
            elif ctag == "link":
                rel = child.attrib.get("rel", "alternate")
                if rel == "alternate" or not link:
                    link = child.attrib.get("href", "") or text
            elif ctag in ("pubdate", "published", "updated") and text and not published:
                try:
                    published = email.utils.parsedate_to_datetime(text).date()
                except Exception:
                    try:
                        published = datetime.date.fromisoformat(text[:10])
                    except Exception:
                        published = None
        if title and link:
            items.append({"title": title, "link": link, "date": published})
    return items


def fetch_leads(since: datetime.date) -> list[dict]:
    seen, leads = set(), []
    for feed in LEAD_FEEDS:
        raw = _fetch(feed)
        if not raw:
            continue
        for item in _parse_feed(raw):
            if item["link"] in seen or not _domain_ok(item["link"]):
                continue
            if not item["date"] or item["date"] <= since:
                continue
            seen.add(item["link"])
            leads.append(item)
    leads.sort(key=lambda x: x["date"], reverse=True)
    return leads[:30]


# --------------------------------------------------------------------------- #
# 2. Ask the Cursor agent for a strict JSON payload
# --------------------------------------------------------------------------- #
def build_prompt(today: datetime.date, since: datetime.date, leads: list[dict],
                 hub_sources: list[str], tracker_text: str) -> str:
    lead_lines = "\n".join(
        f"- {l['date'].isoformat()} {l['title']} {l['link']}" for l in leads
    ) or "- (no feed items; search the vendor sites directly)"
    covered = "\n".join(f"- {u}" for u in hub_sources) or "- (none)"
    pages = ", ".join(INTERNAL_PAGES)
    return f"""You are the editor of "This Week in AI" on aicareertransition.com. Readers already have a job (marketing, analytics, product, operations, finance, HR) and want to use AI well at work. They are not engineers and not students.

Today is {today.isoformat()}. The last brief was published on {since.isoformat()}.

TASK
Find what OpenAI (ChatGPT), Anthropic (Claude), Google (Gemini, Workspace), and Microsoft (Copilot, Microsoft 365) shipped AFTER {since.isoformat()} and on or before {today.isoformat()} that changes how a working professional does their job. Use web search and open the vendor's own page for every item. Do not rely on memory. Do not create or edit any files.

Leads from official feeds (incomplete, and many are not relevant):
{lead_lines}

Already covered on the site (do not repeat these URLs, or a second card for the same model announcement):
{covered}

What counts: new features people can use at work, new models in the products people use, plan or availability changes, new admin, privacy, or data controls, agent features.
What does not count: funding, hiring, research with no product, events, partnerships with no feature, rumors, coverage from press or social media, small bug fixes.

If fewer than {MIN_UPDATES} updates qualify, return exactly:
{{"skip": true, "reason": "one sentence"}}

Otherwise return ONLY one JSON object, no prose and no code fences:
{{
  "skip": false,
  "headline": "the one theme that ties the updates together, sentence case, <= 70 chars",
  "lede": "one or two plain sentences under the headline",
  "summary": "3 or 4 sentences: the pattern across the updates and what it changes at work",
  "page_title": "This Week in AI: <short theme>, <= 60 chars total",
  "meta_description": "one sentence, <= 160 chars",
  "updates": [
    {{
      "vendor": "OpenAI | Anthropic | Google | Microsoft",
      "date": "YYYY-MM-DD, the date on the vendor's page",
      "who": "who can use it now: plans, preview or GA, rollout, regions",
      "title": "<= 70 chars, says what changed",
      "body": "2 or 3 specific sentences: what it does, in plain words",
      "source_url": "the vendor page you read",
      "action": "one concrete thing to try at work this week, 1 or 2 sentences",
      "action_link": "one of: {pages}",
      "watch_out": "the real limit, risk, or check, 1 or 2 sentences"
    }}
  ],
  "tip": {{"title": "<= 60 chars", "body": "2 or 3 sentences: one work habit this week's news calls for"}},
  "prompt_of_week": "a prompt a professional can paste today, tied to this week's news, with [PLACEHOLDERS]",
  "tracker": [
    {{"vendor": "OpenAI", "models": "current models people should use, separated by ' · '", "source_url": "official page", "source_label": "short label"}}
  ],
  "post": {{
    "title": "<= 80 chars",
    "description": "one sentence, <= 160 chars",
    "body_html": "the full brief, see POST RULES"
  }}
}}

UPDATES: {MIN_UPDATES} to {MAX_UPDATES} items, most useful first. Each one must be dated after {since.isoformat()}.

TRACKER: include it only if a vendor's current model lineup changed. Then give exactly four rows, one per vendor, in the order OpenAI, Anthropic, Google, Microsoft, and keep the rows that did not change as they are now:
{tracker_text}
If nothing changed, leave "tracker" out.

POST RULES (body_html):
- 900 to 1600 words. Plain HTML using only <section>, <h2>, <h3>, <p>, <ul>, <ol>, <li>, <a>, <strong>, <em>, <table>, <thead>, <tbody>, <tr>, <th>, <td>. No style attributes, no images, no scripts.
- 3 to 5 <section> blocks with numbered <h2> headings ("1. ...") grouped by theme, not by vendor.
- Inside each section, lead each item with <strong>Vendor, Month D.</strong>, link the vendor page inline with target="_blank" rel="noopener noreferrer", and say <em>Who gets it:</em>.
- In each section add <h3>What changes for you</h3> and <h3>How to use it without getting burned</h3> with specific steps, checks, or a template a reader can copy.
- Do not add a summary list, a sources list, a title, or a byline. The page adds those.

VOICE (output that breaks these is rejected):
- Write like a careful colleague. Short, plain sentences. Specific over general.
- No em dashes. Use commas, periods, or parentheses.
- Never use: "no hype", "durable skill", "game-changer", "unlock", "leverage", "seamless", "delve", "cutting-edge", "supercharge", "in today's fast-paced", "Here is how", "the signal for professionals".
- Never invent a number, plan, date, or quote. If the vendor page does not say who gets it, write "The vendor has not said who gets it."
- Do not name retired models (GPT-3.5, Claude 2, Bard, Gemini 1.5, Gemini 2.0 Flash).
"""


def call_agent(prompt: str) -> str:
    try:
        from cursor_sdk import Agent, AgentOptions, LocalAgentOptions, CursorAgentError
    except Exception as e:
        print(f"[warn] cursor-sdk not importable: {e}", file=sys.stderr)
        return ""
    api_key = os.environ.get("CURSOR_API_KEY")
    if not api_key:
        return ""
    model = os.environ.get("WEEKLY_MODEL") or "composer-2.5"
    # An empty working dir keeps the agent away from the repo files.
    workdir = tempfile.mkdtemp(prefix="ai-news-")
    try:
        result = Agent.prompt(
            prompt,
            AgentOptions(api_key=api_key, model=model, local=LocalAgentOptions(cwd=workdir)),
        )
    except CursorAgentError as err:
        print(f"[warn] agent startup failed: {err}", file=sys.stderr)
        return ""
    if getattr(result, "status", None) == "error":
        print(f"[warn] agent run failed: {getattr(result, 'id', '?')}", file=sys.stderr)
        return ""
    return result.result or ""


def extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in agent output")
    return json.loads(text[start : end + 1])


# --------------------------------------------------------------------------- #
# 3. Validate (fail closed: any error means nothing is published)
# --------------------------------------------------------------------------- #
def _strings(obj) -> list[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in _strings(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in _strings(v)]
    return []


def _plain_words(html: str) -> int:
    return len(re.sub(r"<[^>]+>", " ", html).split())


def validate(payload: dict, since: datetime.date, today: datetime.date,
             hub_sources: list[str]) -> list[str]:
    errs: list[str] = []
    for field in ("headline", "lede", "summary", "page_title", "meta_description", "prompt_of_week"):
        if not str(payload.get(field) or "").strip():
            errs.append(f"missing {field}")
    if len(str(payload.get("page_title", ""))) > 70:
        errs.append("page_title too long")

    updates = payload.get("updates")
    if not isinstance(updates, list) or not (MIN_UPDATES <= len(updates) <= MAX_UPDATES):
        errs.append(f"updates must be a list of {MIN_UPDATES}-{MAX_UPDATES} items")
        updates = updates if isinstance(updates, list) else []
    for i, u in enumerate(updates):
        for f in ("vendor", "date", "who", "title", "body", "source_url", "action", "action_link", "watch_out"):
            if not str(u.get(f) or "").strip():
                errs.append(f"update[{i}] missing '{f}'")
        if u.get("vendor") not in VENDORS:
            errs.append(f"update[{i}] vendor must be one of {VENDORS}")
        src = u.get("source_url", "")
        if src and not _domain_ok(src):
            errs.append(f"update[{i}] source is not an official vendor page: {src}")
        if update_already_on_hub(u, hub_sources):
            errs.append(f"update[{i}] is already on the hub: {src}")
        try:
            day = datetime.date.fromisoformat(str(u.get("date", ""))[:10])
            if not (since < day <= today):
                errs.append(f"update[{i}] date {day} is not after {since} and on or before {today}")
        except ValueError:
            errs.append(f"update[{i}] date is not YYYY-MM-DD")
        link = u.get("action_link", "")
        if link and (link.startswith("http") or not (ROOT / link).exists()):
            errs.append(f"update[{i}] action_link is not an internal page: {link}")
        if len(str(u.get("body", "")).split()) < 20:
            errs.append(f"update[{i}] body is too thin")

    tip = payload.get("tip") or {}
    if not tip.get("title") or not tip.get("body"):
        errs.append("missing tip title or body")

    tracker = payload.get("tracker")
    if tracker:
        if not isinstance(tracker, list) or [r.get("vendor") for r in tracker] != list(VENDORS):
            errs.append("tracker must have four rows: OpenAI, Anthropic, Google, Microsoft")
        else:
            for r in tracker:
                if not r.get("models") or not _domain_ok(r.get("source_url", "")):
                    errs.append(f"tracker row {r.get('vendor')} needs models and an official source")

    post = payload.get("post") or {}
    for f in ("title", "description", "body_html"):
        if not post.get(f):
            errs.append(f"post missing '{f}'")
    body = post.get("body_html", "")
    if UNSAFE_TAG_RE.search(body):
        errs.append("post.body_html has a disallowed tag")
    if re.search(r"<\s*(html|head|body|nav|footer|h1)\b", body, re.I):
        errs.append("post.body_html must be article body only")
    if _plain_words(body) < MIN_POST_WORDS:
        errs.append(f"post.body_html is under {MIN_POST_WORDS} words")
    if not any(_domain_ok(m) for m in re.findall(r'href="(https://[^"]+)"', body)):
        errs.append("post.body_html needs official links")

    text = "\n".join(_strings(payload))
    if DEPRECATED_RE.search(text):
        errs.append("payload names a retired model")
    if EM_DASH_RE.search(text):
        errs.append("payload contains an em dash")
    banned = sorted({m.group(0).lower() for m in BANNED_RE.finditer(text)})
    if banned:
        errs.append("payload uses banned phrases: " + ", ".join(banned))
    return errs


# --------------------------------------------------------------------------- #
# 4. Render into the marker blocks (only after validation passes)
# --------------------------------------------------------------------------- #
def esc(s) -> str:
    return (
        str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace('"', "&quot;")
    )


_MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
RETIRED_BRIEFS = {"weekly-ai-brief-2026-09-21.html"}
_ICON_EXT = (
    '<svg class="ax-ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M7 7h10v10"/><path d="M7 17 17 7"/></svg>'
)
_ICON_GO = (
    '<svg class="ax-ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>'
)
_WATCH_BOX = 'class="ax-try" style="background:#FFF8EB;box-shadow:inset 0 0 0 1px #F3DDB3;"'
_WATCH_KEY = 'class="ax-try__k" style="color:#9A5B00;"'


def short_date(day: datetime.date) -> str:
    return f"{_MONTHS[day.month - 1]} {day.day}"


def long_date(day: datetime.date) -> str:
    return f"{short_date(day)}, {day.year}"


def _day(u: dict) -> datetime.date:
    return datetime.date.fromisoformat(str(u["date"])[:10])


def render_updates(updates: list[dict]) -> str:
    out = []
    for u in updates:
        day = _day(u)
        source = esc(u["source_url"])
        internal = esc(u["action_link"])
        out.append(
            f'''        <article class="ax-wcard">
          <div class="ax-wcard__top"><span class="ax-chip ax-chip--vendor" data-vendor="{u["vendor"].lower()}">{esc(u["vendor"])}</span></div>
          <p class="ax-wcard__when">{esc(u["vendor"])} · <time datetime="{day.isoformat()}">{long_date(day)}</time> · {esc(u["who"])}</p>
          <h3 class="ax-wcard__title">{esc(u["title"])}</h3>
          <p class="ax-wcard__why">{esc(u["body"])} <a href="{source}" target="_blank" rel="noopener noreferrer">Source</a></p>
          <div class="ax-try"><span class="ax-try__k">Try this:</span><p>{esc(u["action"])} <a href="{internal}">Go</a></p></div>
          <div {_WATCH_BOX}><span {_WATCH_KEY}>Watch out:</span><p>{esc(u["watch_out"])}</p></div>
          <div class="ax-wcard__foot"><a class="ax-link" href="{source}" target="_blank" rel="noopener noreferrer">Source {_ICON_EXT}</a><a class="ax-link" href="{internal}">Go {_ICON_GO}</a></div>
        </article>'''
        )
    return '<div class="ax-weeklyblock"><div class="ax-weekly">\n' + "\n".join(out) + "\n</div></div>"


def render_strip(published: datetime.date, carried: list[datetime.date]) -> str:
    """Four past briefs plus the latest. Past weeks link only when an indexable archive exists."""
    by_day: dict[datetime.date, str | None] = {}
    for path in sorted((ROOT / "blog").glob("weekly-ai-brief-*.html")):
        match = re.search(r"(20\d{2}-\d{2}-\d{2})", path.name)
        if not match:
            continue
        day = datetime.date.fromisoformat(match.group(1))
        if day >= published:
            continue
        head = path.read_text(encoding="utf-8", errors="ignore")[:6000].lower()
        linked = path.name not in RETIRED_BRIEFS and "noindex" not in head
        by_day[day] = f"blog/{path.name}" if linked else None
    for day in carried:
        if day < published and day not in by_day:
            by_day[day] = None
    cells = []
    for day in sorted(by_day)[-4:]:
        href = by_day[day]
        label = (
            f'<span class="ax-strip__k">Brief</span>'
            f'<span class="ax-strip__d"><time datetime="{day.isoformat()}">{short_date(day)}</time></span>'
        )
        inner = f'<a href="{href}">{label}</a>' if href else f"<div>{label}</div>"
        cells.append(f'          <li class="ax-strip__wk ax-strip__wk--past">{inner}</li>')
    cells.append(
        '          <li class="ax-strip__wk ax-strip__wk--current"><div>'
        '<span class="ax-strip__k">Latest</span>'
        f'<span class="ax-strip__d"><time id="hub-updated" datetime="{published.isoformat()}">'
        f"<!-- WEEKLY:DATE -->{long_date(published)}</time></span></div></li>"
    )
    return (
        '          <div class="ax-weeklyblock">\n'
        '        <ol class="ax-strip" aria-label="Weekly briefs">\n'
        + "\n".join(cells)
        + "\n        </ol>\n          </div>"
    )


def render_summary(summary: str, since: datetime.date, slug: str) -> str:
    return f'''        <div class="section-header ax-align-start animate-on-scroll" style="margin-bottom: var(--space-lg);">
          <span class="ax-kicker">Since {short_date(since)}</span>
          <h2>What changed</h2>
          <p>{esc(summary)}</p>
          <p style="margin-top: var(--space-sm);"><a href="blog/{slug}.html" style="font-weight: 600;">Read the full brief</a>: what shipped, who gets it, and the checks that keep it safe at work.</p>
        </div>'''


def render_lede(headline: str, lede: str) -> str:
    return (
        f'          <p class="hero-description" style="margin-bottom: var(--space-sm); max-width: 720px; font-weight: 600;">{esc(headline)}</p>\n'
        f'          <p class="hero-description" style="margin-bottom: var(--space-md); max-width: 720px;">\n'
        f"            {esc(lede)}\n"
        f"          </p>"
    )


def render_tip(tip: dict, slug: str) -> str:
    return (
        f'            <h3 style="font-size:1.15rem;margin-bottom:var(--space-sm);">{esc(tip["title"])}</h3>\n'
        f'            <p style="line-height:1.75;color:var(--color-text-secondary);">{esc(tip["body"])}</p>\n'
        f'            <p style="margin-top:var(--space-md);"><a href="blog/{slug}.html" '
        f'style="color:var(--color-accent-primary);font-weight:600;">More in the full brief</a></p>'
    )


def render_tracker(rows: list[dict]) -> str:
    cell = 'style="padding:10px 12px;"'
    body = []
    for i, r in enumerate(rows):
        border = ' style="border-bottom:1px solid var(--color-border);"' if i < len(rows) - 1 else ""
        label = esc(r.get("source_label") or re.sub(r"^https://(www\.)?", "", r["source_url"]))
        body.append(
            f"              <tr{border}>\n"
            f'                <td style="padding:10px 12px; font-weight:600;">{esc(r["vendor"])}</td>\n'
            f"                <td {cell}>{esc(r['models'])}</td>\n"
            f'                <td {cell}><a href="{esc(r["source_url"])}" target="_blank" rel="noopener noreferrer">{label}</a></td>\n'
            f"              </tr>"
        )
    return (
        '          <table style="width:100%; border-collapse:collapse; font-size:15px; min-width:640px;">\n'
        "            <thead>\n"
        '              <tr style="text-align:left; border-bottom:2px solid var(--color-border);">\n'
        f'                <th {cell}>Vendor</th>\n                <th {cell}>What to use</th>\n                <th {cell}>Source</th>\n'
        "              </tr>\n            </thead>\n            <tbody>\n"
        + "\n".join(body)
        + "\n            </tbody>\n          </table>"
    )


def render_latest(limit: int = 3) -> str:
    posts = []
    for p in sorted((ROOT / "blog").glob("*.html")):
        item = build_feed.extract_post(p)
        if item and item["title"]:
            posts.append(item)
    posts.sort(key=lambda x: x["date"], reverse=True)
    out = []
    for post in posts[:limit]:
        rel = post["url"].replace(build_feed.BASE + "/", "")
        out.append(
            f'''          <article class="card" style="padding: var(--space-lg); margin-bottom: var(--space-md);">
            <h3 style="margin:6px 0;font-size:1.1rem;"><a href="{esc(rel)}" style="color:var(--color-text-primary);text-decoration:none;">{esc(post["title"])}</a></h3>
            <a href="{esc(rel)}" style="color:var(--color-accent-primary);font-weight:600;font-size:15px;">Read</a>
          </article>'''
        )
    return "\n".join(out)


def render_home(payload: dict) -> str:
    cards = []
    for u in payload["updates"][:3]:
        cards.append(
            f'''          <div class="card" style="padding: var(--space-lg);">
            <h3 class="card-title">{esc(u["title"])}</h3>
            <p class="card-description">{esc(u["body"])}</p>
            <p class="card-description" style="margin-top: var(--space-sm);"><strong>Check:</strong> {esc(u["watch_out"])}</p>
          </div>'''
        )
    n = len(payload["updates"]) + int(payload.get("kept_cards") or 0)
    return (
        f'        <h2 class="ax-h2">{esc(payload["headline"])}</h2>\n'
        f'        <p class="ax-sh__sub">{esc(payload["lede"])}</p>\n'
        '        <div class="grid grid-3" style="margin: var(--space-lg) 0;">\n'
        + "\n".join(cards)
        + "\n        </div>\n"
        f'        <a class="ax-link" href="this-week.html">All {n} updates, who gets them, and sources {_ICON_GO}</a>'
    )


class HubRewriteError(RuntimeError):
    """A page is missing a block the refresh has to rewrite."""


def replace_block(text: str, start: str, end: str, new_inner: str, required: bool = True) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    indent = re.search(r"([ \t]*)" + re.escape(end), text)
    pad = indent.group(1) if indent else ""
    new, n = pattern.subn(lambda _m: f"{start}\n{new_inner}\n{pad}{end}", text, count=1)
    if n != 1 and required:
        raise HubRewriteError(f"missing {start}")
    return new


def _must_sub(text: str, pattern: str, value: str, label: str, flags: int = 0) -> str:
    new, n = re.subn(pattern, lambda m: m.group(1) + value + m.group(2), text, count=1, flags=flags)
    if n != 1:
        raise HubRewriteError(f"missing {label}")
    return new


def hub_date(text: str) -> datetime.date:
    m = re.search(r'id="hub-updated" datetime="(\d{4}-\d{2}-\d{2})"', text)
    if not m:
        raise HubRewriteError("missing hub-updated date")
    return datetime.date.fromisoformat(m.group(1))


def hub_sources(text: str) -> list[str]:
    block = re.search(r"<!-- WEEKLY:UPDATES:START -->(.*?)<!-- WEEKLY:UPDATES:END -->", text, re.DOTALL)
    if not block:
        return []
    return sorted(set(re.findall(r'href="(https://[^"]+)"', block.group(1))))


def kept_terra_card(text: str, incoming_sources: list[str]) -> str:
    """The live Terra card, when this brief did not already include that announcement.

    The daily rewrite replaces the updates block. Terra is removed from a new
    payload by the already-on-the-hub check, so the existing card has to be
    copied forward or the refresh drops it.
    """
    if any(_TERRA_SOURCE_RE.search(str(src or "")) for src in incoming_sources):
        return ""
    block = re.search(r"<!-- WEEKLY:UPDATES:START -->(.*?)<!-- WEEKLY:UPDATES:END -->", text, re.DOTALL)
    if not block:
        return ""
    for art in re.findall(r'<article class="ax-wcard"[^>]*>.*?</article>', block.group(1), re.DOTALL):
        if "introducing-gpt-6-1-terra" in art:
            return art.strip()
    return ""


def tracker_text(text: str) -> str:
    block = re.search(r"<!-- WEEKLY:TRACKER:START -->(.*?)<!-- WEEKLY:TRACKER:END -->", text, re.DOTALL)
    if not block:
        return ""
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", block.group(1), re.DOTALL):
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL)]
        if cells:
            rows.append(" | ".join(cells))
    return "\n".join(rows)


def carried_week_dates(text: str, published: datetime.date) -> list[datetime.date]:
    block = re.search(r"<!-- WEEKLY:STRIP:START -->(.*?)<!-- WEEKLY:STRIP:END -->", text, re.DOTALL)
    found = []
    if block:
        found = [datetime.date.fromisoformat(d) for d in re.findall(r'datetime="(\d{4}-\d{2}-\d{2})"', block.group(1))]
    return [d for d in found if d < published]


def rewrite_hub(text: str, payload: dict, published: datetime.date) -> str:
    since = hub_date(text)
    slug = payload["post"]["slug"]
    title = esc(payload["page_title"].strip())
    desc = esc(payload["meta_description"].strip())
    text = replace_block(text, "<!-- WEEKLY:LEDE:START -->", "<!-- WEEKLY:LEDE:END -->",
                         render_lede(payload["headline"], payload["lede"]))
    text = replace_block(text, "<!-- WEEKLY:STRIP:START -->", "<!-- WEEKLY:STRIP:END -->",
                         render_strip(published, carried_week_dates(text, published)))
    text = replace_block(text, "<!-- WEEKLY:SUMMARY:START -->", "<!-- WEEKLY:SUMMARY:END -->",
                         render_summary(payload["summary"], since, slug))
    incoming = [str(u.get("source_url") or "") for u in payload["updates"]]
    updates_html = render_updates(payload["updates"])
    extra = kept_terra_card(text, incoming)
    payload["kept_cards"] = 1 if extra else 0
    if extra:
        updates_html = updates_html.replace("\n</div></div>", "\n" + extra + "\n</div></div>", 1)
    text = replace_block(text, "<!-- WEEKLY:UPDATES:START -->", "<!-- WEEKLY:UPDATES:END -->",
                         updates_html)
    text = replace_block(text, "<!-- WEEKLY:TIP:START -->", "<!-- WEEKLY:TIP:END -->",
                         render_tip(payload["tip"], slug))
    if payload.get("tracker"):
        text = replace_block(text, "<!-- WEEKLY:TRACKER:START -->", "<!-- WEEKLY:TRACKER:END -->",
                             render_tracker(payload["tracker"]))
    text = replace_block(text, "<!-- WEEKLY:PROMPT:START -->", "<!-- WEEKLY:PROMPT:END -->",
                         '          <p style="line-height:1.8;color:var(--color-text-secondary);'
                         'font-family:var(--font-mono, monospace);font-size:15px;">'
                         f'"{esc(payload["prompt_of_week"])}"</p>')
    text = _must_sub(text, r"(<title>).*?(</title>)", title, "title", flags=re.DOTALL)
    for attr, label in (
        (r'<meta\s+property="og:title"\s+content="', "og:title"),
        (r'<meta\s+name="twitter:title"\s+content="', "twitter:title"),
    ):
        text = _must_sub(text, f"({attr})[^\"]*(\")", title, label)
    for attr, label in (
        (r'<meta\s+name="description"\s+content="', "meta description"),
        (r'<meta\s+property="og:description"\s+content="', "og:description"),
        (r'<meta\s+name="twitter:description"\s+content="', "twitter:description"),
        (r'"description":\s*"', "JSON-LD description"),
    ):
        text = _must_sub(text, f"({attr})[^\"]*(\")", desc, label)
    text = _must_sub(text, r'("dateModified":\s*")[^"]*(")', published.isoformat(), "JSON-LD dateModified")
    return replace_block(text, "<!-- WEEKLY:LATEST:START -->", "<!-- WEEKLY:LATEST:END -->", render_latest())


def rewrite_home(text: str, payload: dict) -> str:
    return replace_block(text, "<!-- WEEKLY:HOME:START -->", "<!-- WEEKLY:HOME:END -->", render_home(payload))


# --------------------------------------------------------------------------- #
# 5. The dated brief and the indexes
# --------------------------------------------------------------------------- #
_STYLES = {
    "section": 'style="margin-bottom: var(--space-2xl);"',
    "h2": 'style="font-size: 1.35rem; margin-bottom: var(--space-md);"',
    "h3": 'style="font-size: 1.1rem; margin: var(--space-lg) 0 var(--space-sm);"',
    "p": 'style="line-height: 1.8; color: var(--color-text-secondary);"',
    "ul": 'style="list-style: disc; padding-left: 1.25rem; line-height: 1.8; color: var(--color-text-secondary);"',
    "ol": 'style="list-style: decimal; padding-left: 1.25rem; line-height: 1.8; color: var(--color-text-secondary);"',
    "table": 'style="width:100%; border-collapse:collapse; font-size:15px; min-width:560px;"',
    "th": 'style="text-align:left; padding:10px 12px; border-bottom:2px solid var(--color-border);"',
    "td": 'style="padding:10px 12px; border-bottom:1px solid var(--color-border); vertical-align:top;"',
}


def style_body(body: str) -> str:
    body = re.sub(r'\s(style|class|onclick|on\w+)="[^"]*"', "", body)
    for tag, style in _STYLES.items():
        body = re.sub(rf"<{tag}>", f"<{tag} {style}>", body)
    body = re.sub(r"<table ", '<div class="card" style="padding: var(--space-md); overflow-x:auto; margin: var(--space-md) 0;"><table ', body)
    return body.replace("</table>", "</table></div>")


BLOG_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <meta name="description" content="{desc}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://aicareertransition.com/blog/{slug}.html">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="https://aicareertransition.com/blog/{slug}.html">
  <meta property="og:image" content="https://aicareertransition.com/images/og-image.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">
  <link rel="alternate" type="application/rss+xml" title="AI Career Transition: This Week in AI" href="/feed.xml">
  <script type="application/ld+json">
  {ld_post}
  </script>
  <script type="application/ld+json">
  {ld_crumbs}
  </script>
  <link rel="icon" type="image/svg+xml" href="../images/favicon.svg">
  <link rel="stylesheet" href="../css/styles.css?v={css_ver}">
  <title>{title}</title>
  <script>window.addEventListener("load",function(){{var e=document.createElement("script");e.src="/js/load-third-party.js";e.async=true;document.head.appendChild(e);}});</script>
</head>
<body>
  <a href="#main-content" class="skip-link">Skip to main content</a>
  <nav class="navbar" role="navigation" aria-label="Main navigation"><div class="navbar-container"><a href="/" class="navbar-logo" aria-label="AI Career Transition Home"><svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="36" height="36" rx="8" fill="url(#logo-gradient)"/><path d="M18 8L26 24H10L18 8Z" fill="white" fill-opacity="0.9"/><circle cx="18" cy="22" r="3" fill="white"/><defs><linearGradient id="logo-gradient" x1="0" y1="0" x2="36" y2="36"><stop stop-color="#2563eb"/><stop offset="1" stop-color="#1d4ed8"/></linearGradient></defs></svg><span>AI Career Transition</span></a><div class="navbar-menu"><a href="../this-week.html" class="navbar-link">This Week</a><a href="../101.html" class="navbar-link">Learn</a><a href="../prompts.html" class="navbar-link">Prompts</a><a href="../career.html" class="navbar-link">Career</a><a href="../use-cases.html" class="navbar-link">Use cases</a><a href="../blog.html" class="navbar-link active">Blog</a></div><div class="navbar-actions"><a href="../career.html" class="btn btn-primary">Start</a></div><button class="navbar-toggle" aria-label="Toggle navigation" aria-expanded="false"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg></button></div></nav>
  <main id="main-content"><article class="section" style="padding-top: 120px;"><div class="container" style="max-width: 760px;">
    <header style="margin-bottom: var(--space-2xl);">
      <p style="font-size: 0.875rem; color: var(--color-text-muted); margin-bottom: var(--space-md);"><a href="../this-week.html">This Week in AI</a></p>
      <h1 style="font-size: clamp(1.75rem, 4vw, 2.4rem); line-height: 1.2; margin-bottom: var(--space-lg);">{title}</h1>
      <p style="font-size: 1.0625rem; line-height: 1.75; color: var(--color-text-secondary);">{lede}</p>
      <p style="font-size: 1.0625rem; line-height: 1.75; color: var(--color-text-secondary); margin-top: var(--space-md);">This brief covers what shipped from {since_long} through {date_long}, who can actually use it, and the checks that keep it safe at work. Every claim links to the vendor’s own page.</p>
    </header>

    <div class="card" style="padding: var(--space-xl); margin-bottom: var(--space-2xl); background: var(--color-bg-secondary);">
      <h2 style="font-size: 1.15rem; margin-bottom: var(--space-md);">The short version</h2>
      <ul style="list-style: disc; padding-left: 1.25rem; line-height: 1.8; color: var(--color-text-secondary); margin: 0;">
{short_list}
      </ul>
    </div>

{body}

    <section style="margin-bottom: var(--space-2xl);">
      <h2 style="font-size: 1.1rem; margin-bottom: var(--space-sm);">Sources</h2>
      <ul style="list-style: disc; padding-left: 1.25rem; line-height: 1.8; color: var(--color-text-secondary); font-size: 0.95rem;">
{sources}
      </ul>
      <p class="proof-meta" style="margin-top: var(--space-md);">Plans and rollouts change. If a feature is not in your account, check the source page before assuming you have it. Corrections go through the <a href="../feedback.html#contact">contact form</a>. Editorial rules: <a href="../editorial-policy.html">editorial policy</a>.</p>
    </section>

    <p style="margin-top: var(--space-xl);"><a href="../this-week.html" class="btn btn-primary">This Week in AI</a> <a href="../career.html" class="btn btn-secondary" style="margin-left: var(--space-sm);">Career path</a></p>
  </div></article></main>
  <footer class="footer"><div class="container"><div class="footer-bottom"><p>&copy; {year} AI Career Transition. All rights reserved. · <a href="../use-cases.html">Use cases</a> · <a href="../privacy.html">Privacy</a> · <a href="../terms.html">Terms</a></p></div></div></footer>
  <script src="../js/main.js?v={css_ver}" defer></script>
</body>
</html>
'''


def _ld(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def post_ld(post: dict, date: str) -> dict:
    url = f"https://aicareertransition.com/blog/{post['slug']}.html"
    return {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": post["title"], "description": post["description"],
        "datePublished": date, "dateModified": date,
        "author": {"@type": "Organization", "name": "AI Career Transition"},
        "publisher": {"@type": "Organization", "name": "AI Career Transition",
                      "logo": {"@type": "ImageObject", "url": "https://aicareertransition.com/images/og-image.png"}},
        "image": "https://aicareertransition.com/images/og-image.png",
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
    }


def write_post(payload: dict, published: datetime.date, since: datetime.date) -> Path:
    post = payload["post"]
    date = published.isoformat()
    url = f"https://aicareertransition.com/blog/{post['slug']}.html"
    crumbs = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://aicareertransition.com/"},
            {"@type": "ListItem", "position": 2, "name": "This Week in AI", "item": "https://aicareertransition.com/this-week.html"},
            {"@type": "ListItem", "position": 3, "name": post["title"], "item": url},
        ],
    }
    short_list = "\n".join(
        f"        <li>{esc(u['title'])}. <em>{esc(u['who'])}</em></li>" for u in payload["updates"]
    )
    sources = "\n".join(
        f'        <li>{esc(u["vendor"])}: <a href="{esc(u["source_url"])}" target="_blank" rel="noopener noreferrer">{esc(u["title"])}</a> ({short_date(_day(u))})</li>'
        for u in payload["updates"]
    )
    html = BLOG_TEMPLATE.format(
        slug=post["slug"], title=esc(post["title"]), desc=esc(post["description"]),
        ld_post=_ld(post_ld(post, date)), ld_crumbs=_ld(crumbs), css_ver=CSS_VER,
        lede=esc(payload["lede"]), since_long=long_date(since + datetime.timedelta(days=1)),
        date_long=long_date(published), short_list=short_list,
        body=style_body(post["body_html"]), sources=sources, year=published.year,
    )
    out = ROOT / "blog" / f"{post['slug']}.html"
    out.write_text(html, encoding="utf-8")
    return out


def add_to_blog_index(post: dict, date: str) -> None:
    blog = ROOT / "blog.html"
    text = blog.read_text(encoding="utf-8")
    href = f"blog/{post['slug']}.html"
    if href in text:
        return
    minutes = max(3, round(_plain_words(post["body_html"]) / 220))
    card = f'''        <article class="card animate-on-scroll" style="padding: var(--space-xl); margin-bottom: var(--space-lg);">
          <div style="display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-sm); flex-wrap: wrap;"><span class="prompt-card-category" style="margin: 0;">Weekly Brief</span><span style="font-size: 0.8125rem; color: var(--color-text-muted);">{minutes} min read</span></div>
          <h3 style="margin-bottom: var(--space-sm); font-size: 1.25rem; line-height: 1.35;"><a href="{href}" style="color: var(--color-text-primary); text-decoration: none;">{esc(post["title"])}</a></h3>
          <p style="line-height: 1.7; color: var(--color-text-secondary); margin-bottom: var(--space-md);">{esc(post["description"])}</p>
          <a href="{href}" style="color: var(--color-accent-primary); font-weight: 600; font-size: 0.9375rem;">Read full post →</a>
        </article>
'''
    anchor = '<h2 class="animate-on-scroll" style="margin-bottom: var(--space-xl); font-size: 1.375rem;">All Posts</h2>'
    if anchor not in text:
        raise HubRewriteError("blog.html is missing the All Posts heading")
    text = text.replace(anchor, anchor + "\n\n" + card, 1)
    entry = post_ld(post, date)
    entry.pop("@context")
    entry["url"] = entry["mainEntityOfPage"]["@id"]
    entry["mainEntityOfPage"] = entry["url"]
    text = text.replace('"blogPost": [', '"blogPost": [\n      ' + _ld(entry) + ",", 1)
    blog.write_text(text, encoding="utf-8")


def update_llms(post: dict, date: str) -> None:
    path = ROOT / "llms.txt"
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"Last updated: \d{4}-\d{2}-\d{2}", f"Last updated: {date}", text)
    url = f"https://aicareertransition.com/blog/{post['slug']}.html"
    if url not in text:
        text = text.replace("## Current AI Workflow Updates\n", f"## Current AI Workflow Updates\n- {url}\n", 1)
    path.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------- #
# 6. Run
# --------------------------------------------------------------------------- #
def notice(msg: str) -> None:
    prefix = "::warning::" if os.environ.get("GITHUB_ACTIONS") else "[skip] "
    print(prefix + msg)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", type=Path, default=None, help="use a saved JSON payload instead of the agent")
    parser.add_argument("--date", default=None, help="publish date, YYYY-MM-DD (default: today UTC)")
    args = parser.parse_args()

    today = datetime.date.fromisoformat(args.date) if args.date else datetime.datetime.now(_UTC).date()
    hub_path, home_path = ROOT / "this-week.html", ROOT / "index.html"
    hub_text = hub_path.read_text(encoding="utf-8")
    since = hub_date(hub_text)
    if since >= today:
        print(f"[info] already published on {since}; nothing to do")
        return 0

    covered = hub_sources(hub_text)
    if args.payload:
        payload = json.loads(args.payload.read_text(encoding="utf-8"))
    else:
        if not os.environ.get("CURSOR_API_KEY"):
            notice("CURSOR_API_KEY is not set, so no research ran and nothing was published.")
            return 0
        leads = fetch_leads(since)
        print(f"[info] {len(leads)} official feed lead(s) since {since}")
        raw = call_agent(build_prompt(today, since, leads, covered, tracker_text(hub_text)))
        if not raw:
            notice("The research agent returned nothing. Nothing was published.")
            return 0
        try:
            payload = extract_json(raw)
        except Exception as e:
            notice(f"Could not read the agent's answer ({e}). Nothing was published.")
            return 0

    if payload.get("skip"):
        print(f"[info] quiet day, nothing published: {payload.get('reason', 'no reason given')}")
        return 0

    updates = payload.get("updates")
    if isinstance(updates, list):
        fresh, skipped = [], []
        for item in updates:
            if update_already_on_hub(item, covered):
                skipped.append(str(item.get("title") or item.get("source_url") or "update"))
            else:
                fresh.append(item)
        if skipped:
            print("[info] already on the hub, not repeated: " + "; ".join(skipped))
        payload["updates"] = fresh

    slug = f"weekly-ai-brief-{today.isoformat()}"
    payload.setdefault("post", {})["slug"] = slug
    errs = validate(payload, since, today, covered)
    if (ROOT / "blog" / f"{slug}.html").exists():
        errs.append(f"{slug}.html already exists")
    if errs:
        notice("The draft failed checks, so nothing was published: " + "; ".join(errs))
        return 0

    try:
        new_hub = rewrite_hub(hub_text, payload, today)
        new_home = rewrite_home(home_path.read_text(encoding="utf-8"), payload)
    except HubRewriteError as err:
        print(f"[fatal] page rewrite failed: {err}", file=sys.stderr)
        return 1

    write_post(payload, today, since)
    hub_path.write_text(new_hub, encoding="utf-8")
    # Latest list must see the new post, so render it after the post exists.
    hub_path.write_text(
        replace_block(new_hub, "<!-- WEEKLY:LATEST:START -->", "<!-- WEEKLY:LATEST:END -->", render_latest()),
        encoding="utf-8",
    )
    home_path.write_text(new_home, encoding="utf-8")
    add_to_blog_index(payload["post"], today.isoformat())
    update_llms(payload["post"], today.isoformat())

    import build_sitemap
    build_sitemap.main()
    build_feed.main()
    print(f"[ok] published {slug} with {len(payload['updates'])} updates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
