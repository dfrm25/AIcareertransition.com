#!/usr/bin/env python3
"""Weekly content generator — runs unattended in GitHub Actions.

Primary path: pull recent posts from official vendor RSS/news pages and write
a dated brief. Optional: if CURSOR_API_KEY is set, a Cursor agent can rewrite
the copy. If feeds are quiet, a conservative fallback still refreshes the date
so the hub never goes stale.

Env:
  CURSOR_API_KEY   optional
  WEEKLY_MODEL     optional (default: composer-2.5)
"""
from __future__ import annotations

import datetime
import email.utils
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_feed  # noqa: E402

_UTC = getattr(datetime, "UTC", datetime.timezone.utc)

OFFICIAL_DOMAINS = (
    "openai.com", "anthropic.com", "claude.com", "google.com", "blog.google",
    "ai.google.dev", "cloud.google.com", "deepmind.google", "microsoft.com",
    "workspaceupdates.googleblog.com",
)
DEPRECATED_RE = re.compile(
    r"gemini\s*2\.0\s*flash|gemini\s*1\.5|gemini\s*1\.0|\bgpt-3\.5\b|\bgpt-3\b|"
    r"text-davinci|\bclaude\s*2\b|\bclaude\s*instant\b|\bgoogle\s+bard\b|"
    r"\bbard\b(?!\w)|\bo1-preview\b|\bgpt-4\.0\b",
    re.IGNORECASE,
)
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
UPDATE_BORDER = "var(--color-border)"
CSS_VER = "20261004a"

FEEDS = (
    "https://openai.com/news/rss.xml",
    "https://openai.com/blog/rss.xml",
    "https://blog.google/innovation-and-ai/rss/",
    "https://blog.google/rss/",
    "https://www.microsoft.com/en-us/microsoft-copilot/blog/feed/",
)

AGENT_PROMPT_DEFAULT = (
    "You are an agent, not a chatbot. Goal: [TASK]. Context attached: "
    "[FILES OR NOTES]. Tools you may use: [SEARCH / CODE / BROWSER / NONE]. "
    "Constraints: do not invent numbers; stop and ask if a source is missing. "
    "Loop: plan, act, check. Return (1) the deliverable, (2) what you did, "
    "(3) what a human must verify before this ships."
)

FALLBACK_SOURCES = (
    {
        "category": "Models",
        "title": "Check the live ChatGPT model page",
        "body": "OpenAI changes ChatGPT defaults often. Confirm whether you are on GPT-5.6 Luna (free, Think button) or Sol (paid, reasoning slider) before you trust a hard answer.",
        "source_url": "https://help.openai.com/en/articles/20001354-gpt-56-in-chatgpt",
        "action": "Open the model picker and save one before/after on a real work task.",
        "action_link": "blog/how-to-change-ai-model.html",
    },
    {
        "category": "Agents",
        "title": "Claude's current models are built to run, not just reply",
        "body": "Opus 5 and Sonnet 5 are the current Claude lineup for long-running agents, tool use, and computer use. Brief them with a goal, tools, and a stop condition.",
        "source_url": "https://platform.claude.com/docs/en/about-claude/models/overview",
        "action": "Paste an agentic brief from the prompt library into Claude or Claude Code.",
        "action_link": "prompts.html",
    },
    {
        "category": "Tools",
        "title": "Copilot agents are a Microsoft 365 product now",
        "body": "Agent Builder is how workplace agents get created and, with admin approval, land in an org agent store. If you work in Microsoft 365, this is the path that will show up at work.",
        "source_url": "https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/agents-overview",
        "action": "Sketch instructions and one human approval point for a recurring task you already own.",
        "action_link": "blog/agentic-ai-workflows-for-non-engineers.html",
    },
)


def _domain_ok(url: str) -> bool:
    return url.startswith("https://") and any(
        (f"//{d}" in url or f".{d}" in url) for d in OFFICIAL_DOMAINS
    )


def _fetch(url, timeout=12):
    req = urllib.request.Request(
        url, headers={"User-Agent": "AICareerTransitionWeekly/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as err:
        print(f"[warn] fetch failed {url}: {err}", file=sys.stderr)
        return None


def _parse_rss(xml_bytes: bytes) -> list[dict]:
    items = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return items
    for item in root.iter():
        tag = item.tag.lower().split("}")[-1]
        if tag != "item" and tag != "entry":
            continue
        title = link = summary = ""
        published = None
        for child in item:
            ctag = child.tag.lower().split("}")[-1]
            text = (child.text or "").strip()
            if ctag in ("title",) and text:
                title = text
            elif ctag in ("link",):
                link = child.attrib.get("href", "") or text
            elif ctag in ("description", "summary"):
                summary = re.sub(r"<[^>]+>", "", text)
            elif ctag in ("pubdate", "published", "updated") and text:
                try:
                    published = email.utils.parsedate_to_datetime(text).date()
                except Exception:
                    try:
                        published = datetime.date.fromisoformat(text[:10])
                    except Exception:
                        published = None
        if title and link:
            items.append(
                {"title": title, "link": link, "summary": summary[:280], "date": published}
            )
    return items


def fetch_feed_updates(monday: datetime.date) -> list[dict]:
    cutoff = monday - datetime.timedelta(days=10)
    seen = set()
    picked = []
    for feed in FEEDS:
        raw = _fetch(feed)
        if not raw:
            continue
        for item in _parse_rss(raw):
            url = item["link"]
            if url in seen or not _domain_ok(url):
                continue
            if item["date"] and item["date"] < cutoff:
                continue
            seen.add(url)
            body = item["summary"] or item["title"]
            picked.append(
                {
                    "category": "News",
                    "title": item["title"][:90],
                    "body": body,
                    "source_url": url,
                    "action": "Read the source, then apply it to one task you already own this week.",
                    "action_link": "prompts.html",
                    "date": item["date"].isoformat() if item.get("date") else "",
                }
            )
            if len(picked) >= 5:
                return picked
    return picked


def payload_from_updates(updates: list[dict], week_label: str, week_date: str) -> dict:
    if len(updates) < 2:
        updates = list(FALLBACK_SOURCES)
    sections = []
    for i, u in enumerate(updates, 1):
        sections.append(
            f'<section style="margin-bottom: var(--space-2xl);">'
            f'<h2 style="font-size: 1.25rem; margin-bottom: var(--space-md);">{i}. {esc(u["title"])}</h2>'
            f'<p style="line-height: 1.8;">{esc(u["body"])} '
            f'<a href="{esc(u["source_url"])}" target="_blank" rel="noopener noreferrer">Source</a></p>'
            f'<p style="line-height: 1.8;">{esc(u["action"])}</p></section>'
        )
    title = updates[0]["title"][:80]
    desc = "What shipped from OpenAI, Anthropic, Google, and Microsoft, and one thing to do with it."
    reviewed = datetime.date.fromisoformat(week_date)
    return {
        "week_label": week_label,
        "week_date": week_date,
        "headline": title,
        "lede": updates[0]["body"],
        "summary": " ".join(u["title"].rstrip(".") for u in updates[:3]) + ".",
        "page_title": f"This Week in AI, {short_date(reviewed)}, {reviewed.year}",
        "meta_description": desc[:160],
        "updates": updates[:5],
        "prompt_of_week": AGENT_PROMPT_DEFAULT,
        "post": {
            "slug": f"weekly-ai-brief-{week_date}",
            "title": title,
            "description": desc[:160],
            "category": "Weekly Brief",
            "body_html": "\n".join(sections),
        },
    }


# --------------------------------------------------------------------------- #
# 1. Prompt the Cursor agent for a strict JSON payload
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# 1. Prompt the Cursor agent for a strict JSON payload
# --------------------------------------------------------------------------- #
def build_prompt(week_label: str, week_date: str, existing_slugs: list[str]) -> str:
    return f"""You are the editor of "This Week in AI", a career-focused site for professionals.
Produce content for {week_label} ({week_date}).

Return ONLY a single JSON object (no prose, no markdown fences) with this exact shape:
{{
  "week_label": "{week_label}",
  "week_date": "{week_date}",
  "updates": [
    {{
      "category": "one of: Models, Agents, Tools, Governance, Multimodal, Connected AI",
      "title": "short headline, <= 90 chars",
      "body": "1-2 sentences, plain text, no HTML",
      "source_url": "a real primary/official URL",
      "action": "one concrete career action sentence",
      "action_link": "an internal path like blog/multi-agent-workflows-for-professionals.html, 101.html, 201.html, prompts.html, tools-comparison.html, or artifacts.html"
    }}
  ],
  "prompt_of_week": "a genuinely useful prompt a professional can paste, plain text",
  "headline": "hero headline, plain text, <= 80 chars",
  "lede": "one or two sentences under the headline, plain text, no HTML",
  "summary": "one paragraph for the What changed section, plain text, no HTML",
  "page_title": "document title, <= 60 chars, include the week date and year",
  "meta_description": "meta description, 1 sentence, <= 160 chars",
  "post": {{
    "slug": "weekly-ai-brief-{week_date}",
    "title": "blog post title, <= 90 chars",
    "description": "meta description, 1 sentence, <= 160 chars",
    "category": "Weekly Brief",
    "body_html": "valid inner HTML for the article body: 3-5 <section> blocks each with an <h2> and <p> paragraphs, using <a href=... target=_blank rel=noopener noreferrer> for official links"
  }}
}}

HARD RULES (violating any means your output is rejected):
- 2 to 5 updates. Each source_url MUST be on one of these official domains ONLY: {", ".join(OFFICIAL_DOMAINS)}.
- Do NOT name specific stale/retired models (no "Gemini 2.0 Flash", "GPT-3.5", "Claude 2", "Bard", "Gemini 1.5", etc.). Refer to current families generally (e.g. "GPT-5 family", "Gemini with Deep Think", "Claude with extended thinking") and link the vendor's live model page for exact versions.
- post.body_html MUST contain at least two links to official domains above.
- Keep everything factual and conservative; if unsure about a claim, describe the capability generally and link the official docs.
- The post.body_html must NOT include <html>, <head>, <nav>, or <footer> (body content only).

VOICE RULES (write like a knowledgeable human, not marketing copy):
- Plain, direct English. Short sentences. No hype.
- Do NOT use em dashes. Use commas, periods, or parentheses instead.
- Ban these words/phrases: "no hype", "durable skill", "game-changer", "unlock",
  "leverage", "seamless", "delve", "cutting-edge", "supercharge", "in today's
  fast-paced", "Here is how", "the signal for professionals".
- Prefer "What to do" over "Career action". Avoid stacked buzzword lists.

Existing post slugs (do not reuse): {", ".join(existing_slugs[:40])}
"""


def call_agent(prompt: str) -> str:
    try:
        from cursor_sdk import Agent, AgentOptions, LocalAgentOptions, CursorAgentError
    except Exception as e:
        print(f"[warn] cursor-sdk not importable: {e}", file=sys.stderr)
        return ""

    api_key = os.environ.get("CURSOR_API_KEY")
    if not api_key:
        print("[info] CURSOR_API_KEY not set; using official feeds", file=sys.stderr)
        return ""
    model = os.environ.get("WEEKLY_MODEL", "composer-2.5")

    try:
        result = Agent.prompt(
            prompt,
            AgentOptions(
                api_key=api_key,
                model=model,
                local=LocalAgentOptions(cwd=str(ROOT)),
            ),
        )
    except CursorAgentError as err:
        print(f"[warn] agent startup failed: {err}", file=sys.stderr)
        return ""

    if getattr(result, "status", None) == "error":
        print(f"[warn] agent run failed: {getattr(result,'id','?')}", file=sys.stderr)
        return ""

    return result.result or ""


def extract_json(text: str) -> dict:
    text = text.strip()
    # Strip accidental code fences.
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", text.strip())
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in agent output")
    return json.loads(text[start : end + 1])


# --------------------------------------------------------------------------- #
# 2. Validate — fail closed
# --------------------------------------------------------------------------- #
def validate(payload: dict, existing_slugs: list[str], week_slug: str) -> list[str]:
    errs: list[str] = []
    updates = payload.get("updates")
    if not isinstance(updates, list) or not (2 <= len(updates) <= 7):
        errs.append("updates must be a list of 2-7 items")
        updates = updates if isinstance(updates, list) else []
    for i, u in enumerate(updates):
        for f in ("category", "title", "body", "source_url", "action", "action_link"):
            if not u.get(f):
                errs.append(f"update[{i}] missing '{f}'")
        src = u.get("source_url", "")
        if src and not _domain_ok(src):
            errs.append(f"update[{i}] source_url not on official domain: {src}")
        link = u.get("action_link", "")
        if link and not link.startswith("http"):
            if not (ROOT / link).exists():
                errs.append(f"update[{i}] action_link not found: {link}")
        blob = json.dumps(u)
        if DEPRECATED_RE.search(blob):
            errs.append(f"update[{i}] contains a deprecated model name")

    post = payload.get("post") or {}
    slug = post.get("slug", "")
    if not SLUG_RE.match(slug):
        errs.append(f"post.slug invalid: {slug!r}")
    if slug in existing_slugs and slug != week_slug:
        errs.append(f"post.slug already exists: {slug}")
    for f in ("title", "description", "category", "body_html"):
        if not post.get(f):
            errs.append(f"post missing '{f}'")
    body = post.get("body_html", "")
    if DEPRECATED_RE.search(body):
        errs.append("post.body_html contains a deprecated model name")
    if sum(1 for _ in re.finditer(r'href="https://', body)) < 2 or not any(
        _domain_ok(m.group(1)) for m in re.finditer(r'href="(https://[^"]+)"', body)
    ):
        errs.append("post.body_html needs >=2 links incl. an official-domain source")
    for tag in ("<html", "<head", "<nav", "<footer"):
        if tag in body.lower():
            errs.append(f"post.body_html must not contain {tag}")

    if not payload.get("prompt_of_week"):
        errs.append("missing prompt_of_week")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(payload.get("week_date") or "")):
        errs.append("week_date missing or not YYYY-MM-DD")
    for field in ("headline", "lede", "summary", "page_title", "meta_description"):
        if not str(payload.get(field) or "").strip():
            errs.append(f"missing {field}")
    return errs


# --------------------------------------------------------------------------- #
# 3. Render into templates + marker blocks (only after validation passes)
# --------------------------------------------------------------------------- #
def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _vendor(url: str) -> tuple[str, str]:
    host = url.lower()
    if "anthropic.com" in host or "claude.com" in host:
        return "anthropic", "Anthropic"
    if "google" in host:
        return "google", "Google"
    if "microsoft.com" in host:
        return "microsoft", "Microsoft"
    if "openai.com" in host:
        return "openai", "OpenAI"
    return "other", "Source"


def _card_date(value) -> str:
    if not value:
        return ""
    if hasattr(value, "isoformat"):
        iso = value.isoformat()
        label = value.strftime("%b %-d, %Y")
    else:
        iso = str(value)[:10]
        try:
            day = datetime.date.fromisoformat(iso)
            label = day.strftime("%b %-d, %Y")
        except ValueError:
            label = esc(str(value))
            iso = ""
    if not iso:
        return f"<p class=\"ax-wcard__when\">{label}</p>"
    return f'<p class="ax-wcard__when"><time datetime="{esc(iso)}">{label}</time></p>'


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
_MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
RETIRED_BRIEFS = {"weekly-ai-brief-2026-09-21.html"}


def short_date(day: datetime.date) -> str:
    return f"{_MONTHS[day.month - 1]} {day.day}"


def render_updates(updates: list[dict]) -> str:
    out = []
    for u in updates:
        internal = u["action_link"]
        vendor, vendor_label = _vendor(u.get("source_url", ""))
        when = _card_date(u.get("date"))
        source = esc(u["source_url"])
        out.append(
            f'''        <article class="ax-wcard">
          <div class="ax-wcard__top"><span class="ax-chip ax-chip--vendor" data-vendor="{vendor}">{vendor_label}</span></div>
          {when}
          <h3 class="ax-wcard__title">{esc(u["title"])}</h3>
          <p class="ax-wcard__why">{esc(u["body"])}</p>
          <div class="ax-try"><span class="ax-try__k">Try this:</span><p>{esc(u["action"])} <a href="{esc(internal)}">Go</a></p></div>
          <div class="ax-wcard__foot"><a class="ax-link" href="{source}" target="_blank" rel="noopener noreferrer">Source {_ICON_EXT}</a><a class="ax-link" href="{esc(internal)}">Go {_ICON_GO}</a></div>
        </article>'''
        )
    return "<div class=\"ax-weeklyblock\"><div class=\"ax-weekly\">\n" + "\n".join(out) + "\n</div></div>"


def render_strip(reviewed: datetime.date, carried: list[datetime.date] | None = None) -> str:
    """Week strip. Link a past week only when an indexable archive file exists.

    Weeks that were reviewed on the hub but never got an archive file stay in
    the strip as unlinked cells. The strip keeps the three most recent of
    those weeks so five cells still fit. On Oct 5 that includes Sep 27.
    """
    nxt = following_review(reviewed)
    by_day: dict[datetime.date, tuple[bool, str | None]] = {}
    for path in sorted((ROOT / "blog").glob("weekly-ai-brief-*.html")):
        match = re.search(r"(20\d{2}-\d{2}-\d{2})", path.name)
        if not match:
            continue
        day = datetime.date.fromisoformat(match.group(1))
        if day >= reviewed:
            continue
        head = path.read_text(encoding="utf-8", errors="ignore")[:6000].lower()
        linked = path.name not in RETIRED_BRIEFS and "noindex" not in head
        by_day[day] = (linked, f"blog/{path.name}")
    for day in carried or []:
        if day < reviewed and day not in by_day:
            by_day[day] = (False, None)
    cells = []
    for day in sorted(by_day)[-3:]:
        linked, href = by_day[day]
        label = (
            f'<span class="ax-strip__k">Brief</span>'
            f'<span class="ax-strip__d"><time datetime="{day.isoformat()}">{short_date(day)}</time></span>'
        )
        inner = f'<a href="{href}">{label}</a>' if linked and href else f"<div>{label}</div>"
        cells.append(f'          <li class="ax-strip__wk ax-strip__wk--past">{inner}</li>')
    cells.append(
        '          <li class="ax-strip__wk ax-strip__wk--current"><div>'
        '<span class="ax-strip__k">Reviewed</span>'
        f'<span class="ax-strip__d"><time id="hub-updated" datetime="{reviewed.isoformat()}">'
        f'<!-- WEEKLY:DATE -->{short_date(reviewed)}, {reviewed.year}</time></span></div></li>'
    )
    cells.append(
        '          <li class="ax-strip__wk ax-strip__wk--next"><div>'
        '<span class="ax-strip__k">Next</span>'
        f'<span class="ax-strip__d"><time datetime="{nxt.isoformat()}">{short_date(nxt)}</time>'
        '</span></div></li>'
    )
    return (
        '<div class="ax-weeklyblock">\n'
        '        <ol class="ax-strip" aria-label="Weekly briefs">\n'
        + "\n".join(cells)
        + "\n        </ol>\n"
        "          </div>"
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
            <a href="{esc(rel)}" style="color:var(--color-accent-primary);font-weight:600;font-size:0.9rem;">Read</a>
          </article>'''
        )
    return "\n".join(out)


class HubRewriteError(RuntimeError):
    """The hub is missing a field the weekly run has to rewrite."""


def replace_block(text: str, start: str, end: str, new_inner: str, required: bool = False) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    new, n = pattern.subn(f"{start}\n{new_inner}\n        {end}", text, count=1)
    if n != 1:
        if required:
            raise HubRewriteError(f"missing {start}")
        return text
    return new


def _must_sub(text: str, pattern: str, repl: str, label: str, flags: int = 0) -> str:
    new, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        raise HubRewriteError(f"missing {label}")
    return new


def carried_week_dates(text: str, reviewed: datetime.date) -> list[datetime.date]:
    """Prior hub weeks to keep when no archive file exists for them."""
    found: list[datetime.date] = []
    prev = re.search(r'id="hub-updated" datetime="(\d{4}-\d{2}-\d{2})"', text)
    if prev:
        found.append(datetime.date.fromisoformat(prev.group(1)))
    block = re.search(
        r"<!-- WEEKLY:STRIP:START -->(.*)<!-- WEEKLY:STRIP:END -->",
        text,
        re.DOTALL,
    )
    if block:
        for match in re.finditer(r'datetime="(\d{4}-\d{2}-\d{2})"', block.group(1)):
            found.append(datetime.date.fromisoformat(match.group(1)))
    return [day for day in found if day < reviewed]


def previous_brief_date(text: str, reviewed: datetime.date) -> datetime.date:
    """Date the Since label should name: the outgoing brief, not the new one.

    hub-updated already equals the new Reviewed date on a second run. The
    label still has to name the week that just closed.
    """
    prior = carried_week_dates(text, reviewed)
    if not prior:
        raise HubRewriteError("no previous brief date for the Since label")
    return max(prior)


def render_lede(headline: str, lede: str) -> str:
    return (
        f'<p class="hero-description" style="margin-bottom: var(--space-sm); max-width: 720px; font-weight: 600;">{esc(headline)}</p>\n'
        f'          <p class="hero-description" style="margin-bottom: var(--space-md); max-width: 720px;">\n'
        f'            {esc(lede)}\n'
        f'          </p>'
    )


_HUB_FIELDS = (
    "week_date",
    "headline",
    "lede",
    "summary",
    "page_title",
    "meta_description",
    "updates",
    "prompt_of_week",
)


def rewrite_hub(text: str, payload: dict) -> str:
    """Rewrite the weekly hub in memory. Raises if a required field is missing."""
    missing = [field for field in _HUB_FIELDS if not payload.get(field)]
    if missing:
        raise HubRewriteError("payload missing " + ", ".join(missing))
    reviewed = datetime.date.fromisoformat(payload["week_date"])
    since = previous_brief_date(text, reviewed)
    title = esc(str(payload["page_title"]).strip())
    desc = esc(str(payload["meta_description"]).strip())
    text = replace_block(
        text, "<!-- WEEKLY:LEDE:START -->", "<!-- WEEKLY:LEDE:END -->",
        render_lede(str(payload["headline"]).strip(), str(payload["lede"]).strip()),
        required=True,
    )
    text = replace_block(
        text, "<!-- WEEKLY:STRIP:START -->", "<!-- WEEKLY:STRIP:END -->",
        render_strip(reviewed, carried_week_dates(text, reviewed)),
        required=True,
    )
    text = _must_sub(
        text,
        r'(<span class="ax-kicker">)Since [^<]*(</span>)',
        rf"\g<1>Since {short_date(since)}\2",
        "summary kicker",
    )

    def _summary(match: re.Match) -> str:
        inner, n = re.subn(
            r"<p>.*?</p>",
            f"<p>{esc(str(payload['summary']).strip())}</p>",
            match.group(1),
            count=1,
            flags=re.DOTALL,
        )
        if n != 1:
            raise HubRewriteError("missing WEEKLY:SUMMARY paragraph")
        return f"<!-- WEEKLY:SUMMARY:START -->{inner}<!-- WEEKLY:SUMMARY:END -->"

    text, n_summary = re.subn(
        r"<!-- WEEKLY:SUMMARY:START -->(.*?)<!-- WEEKLY:SUMMARY:END -->",
        _summary,
        text,
        count=1,
        flags=re.DOTALL,
    )
    if n_summary != 1:
        raise HubRewriteError("missing WEEKLY:SUMMARY block")
    text = replace_block(
        text, "<!-- WEEKLY:UPDATES:START -->", "<!-- WEEKLY:UPDATES:END -->",
        render_updates(payload["updates"]),
        required=True,
    )
    text = replace_block(
        text, "<!-- WEEKLY:LATEST:START -->", "<!-- WEEKLY:LATEST:END -->",
        render_latest(),
        required=True,
    )
    prompt_html = (
        f'          <p style="line-height:1.8;color:var(--color-text-secondary);'
        f'font-family:var(--font-mono, monospace);font-size:0.95rem;">'
        f'"{esc(payload["prompt_of_week"])}"</p>'
    )
    text = replace_block(
        text, "<!-- WEEKLY:PROMPT:START -->", "<!-- WEEKLY:PROMPT:END -->",
        prompt_html,
        required=True,
    )
    text = _must_sub(text, r"<title>.*?</title>", f"<title>{title}</title>", "title", flags=re.DOTALL)
    text = _must_sub(
        text,
        r'(<meta\s+property="og:title"\s+content=")[^"]*(")',
        rf"\g<1>{title}\g<2>",
        "og:title",
    )
    text = _must_sub(
        text,
        r'(<meta\s+name="twitter:title"\s+content=")[^"]*(")',
        rf"\g<1>{title}\g<2>",
        "twitter:title",
    )
    text = _must_sub(
        text,
        r'(<meta\s+name="description"\s+content=")[^"]*(")',
        rf"\g<1>{desc}\g<2>",
        "meta description",
    )
    text = _must_sub(
        text,
        r'(<meta\s+property="og:description"\s+content=")[^"]*(")',
        rf"\g<1>{desc}\g<2>",
        "og:description",
    )
    text = _must_sub(
        text,
        r'(<meta\s+name="twitter:description"\s+content=")[^"]*(")',
        rf"\g<1>{desc}\g<2>",
        "twitter:description",
    )
    text = _must_sub(
        text,
        r'("description":\s*")[^"]*(")',
        rf"\g<1>{desc}\g<2>",
        "JSON-LD description",
    )
    text = _must_sub(
        text,
        r'("dateModified":\s*")[^"]*(")',
        rf"\g<1>{reviewed.isoformat()}\g<2>",
        "JSON-LD dateModified",
    )
    return text


def next_monday(day: datetime.date) -> datetime.date:
    days_ahead = (7 - day.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return day + datetime.timedelta(days=days_ahead)


def following_review(reviewed: datetime.date) -> datetime.date:
    """Next cell on the strip. Keep at least seven days out.

    A Sunday review would otherwise point at the next morning. Sep 27 then
    shows Oct 5, and Oct 4 shows Oct 12.
    """
    nxt = next_monday(reviewed)
    if (nxt - reviewed).days < 7:
        nxt += datetime.timedelta(days=7)
    return nxt


def human_date(day: datetime.date) -> str:
    return day.strftime("%B %-d, %Y")


def hub_date_label(day: datetime.date) -> str:
    return f"{short_date(day)}, {day.year}"


def apply_hub_metadata(payload: dict) -> None:
    """Keep the hub title and description inside the search limits.

    A bad title or description is replaced with the fallback. If the fallback
    is still over the limit, raise and do not write the hub.
    """
    reviewed = datetime.date.fromisoformat(str(payload["week_date"]))
    label = hub_date_label(reviewed)
    updates = payload.get("updates") or []
    titles = [str(u.get("title") or "").strip() for u in updates if str(u.get("title") or "").strip()]

    def title_ok(value: str) -> bool:
        return value.startswith("This Week in AI") and label in value and len(value) <= 60

    def desc_ok(value: str) -> bool:
        return len(value) <= 160 and f"Reviewed {label}" in value

    title = str(payload.get("page_title") or "").strip()
    if not title_ok(title):
        hook = titles[0] if titles else "what changed"
        title = f"This Week in AI, {label}: {hook}"
        if not title_ok(title):
            raise HubRewriteError(
                f"title failed validation ({len(title)} chars, max 60, "
                f"must start with 'This Week in AI' and include {label}): {title}"
            )
        payload["page_title"] = title

    desc = str(payload.get("meta_description") or "").strip()
    if not desc_ok(desc):
        desc = f"Reviewed {label}: " + ". ".join(titles)
        if not desc_ok(desc):
            raise HubRewriteError(
                f"description failed validation ({len(desc)} chars, max 160, "
                f"must include 'Reviewed {label}'): {desc}"
            )
        payload["meta_description"] = desc


def _shift_archive_hrefs(html: str) -> str:
    def repl(match: re.Match) -> str:
        href = match.group(1)
        if href.startswith(("http://", "https://", "#", "/", "mailto:")):
            return match.group(0)
        return f'href="../{href}"'

    return re.sub(r'href="([^"]+)"', repl, html)


def archive_outgoing_hub(new_date: datetime.date) -> Path | None:
    """Snapshot the live hub before a rollover. Idempotent.

    A second run for the same new date finds the archive file and leaves it.
    A run that does not move the reviewed date does not write an archive.
    """
    hub_path = ROOT / "this-week.html"
    if not hub_path.exists():
        return None
    text = hub_path.read_text(encoding="utf-8")
    current = re.search(r'id="hub-updated" datetime="(\d{4}-\d{2}-\d{2})"', text)
    if not current:
        return None
    old = datetime.date.fromisoformat(current.group(1))
    if old >= new_date:
        return None
    slug = f"weekly-ai-brief-{old.isoformat()}"
    dest = ROOT / "blog" / f"{slug}.html"
    if dest.exists():
        return dest

    title_m = re.search(r"<title>(.*?)</title>", text, re.DOTALL | re.IGNORECASE)
    desc_m = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', text, re.IGNORECASE)
    updates_m = re.search(
        r"<!-- WEEKLY:UPDATES:START -->(.*)<!-- WEEKLY:UPDATES:END -->",
        text,
        re.DOTALL,
    )
    lede_m = re.search(
        r"<!-- WEEKLY:LEDE:START -->(.*)<!-- WEEKLY:LEDE:END -->",
        text,
        re.DOTALL,
    )
    if not (title_m and desc_m and updates_m):
        raise HubRewriteError("cannot archive the outgoing brief: title, description, or cards missing")
    title = re.sub(r"\s+", " ", title_m.group(1)).strip()
    title = re.sub(r"\s*\|\s*AI Career Transition\s*$", "", title)
    description = desc_m.group(1).strip()
    body = (lede_m.group(1) if lede_m else "") + "\n" + updates_m.group(1)
    body = _shift_archive_hrefs(body)
    post = {
        "slug": slug,
        "title": title,
        "description": description,
        "category": "Weekly Brief",
        "body_html": body,
    }
    write_post(post, old.isoformat(), human_date(old))
    prepend_blog_card(post, old.isoformat(), human_date(old))
    update_llms(post, old.isoformat())
    return dest


def update_hub(payload: dict) -> None:
    apply_hub_metadata(payload)
    archive_outgoing_hub(datetime.date.fromisoformat(str(payload["week_date"])))
    hub = ROOT / "this-week.html"
    text = rewrite_hub(hub.read_text(encoding="utf-8"), payload)
    hub.write_text(text, encoding="utf-8")
    update_home(payload)
    update_receipt_stamp(payload["week_date"])


def update_receipt_stamp(week_date: str) -> None:
    """Refresh home receipt markers only when they are already on the page.

    The home hero no longer includes WEEKLY:RECEIPT or WEEKLY:STAMP.
    Missing markers are a no-op: the run does not fail and does not insert them.
    """
    home = ROOT / "index.html"
    if not home.exists():
        return
    text = home.read_text(encoding="utf-8")
    if "<!-- WEEKLY:RECEIPT -->" not in text and "<!-- WEEKLY:STAMP -->" not in text:
        return
    reviewed = datetime.date.fromisoformat(week_date)
    long = reviewed.strftime("%b %-d, %Y")
    short = reviewed.strftime("%b %-d")
    text2, n_long = re.subn(
        r"<!-- WEEKLY:RECEIPT -->.*?<!-- /WEEKLY:RECEIPT -->",
        f"<!-- WEEKLY:RECEIPT -->{long}<!-- /WEEKLY:RECEIPT -->",
        text,
        count=1,
        flags=re.DOTALL,
    )
    text2, n_short = re.subn(
        r"<!-- WEEKLY:STAMP -->.*?<!-- /WEEKLY:STAMP -->",
        f"<!-- WEEKLY:STAMP -->{short}<!-- /WEEKLY:STAMP -->",
        text2,
        count=1,
        flags=re.DOTALL,
    )
    if n_long and n_short and text2 != text:
        home.write_text(text2, encoding="utf-8")


def update_home(payload: dict) -> None:
    home = ROOT / "index.html"
    if not home.exists():
        return
    text = home.read_text(encoding="utf-8")
    reviewed = datetime.date.fromisoformat(str(payload["week_date"]))
    if "<!-- WEEKLY:HOMESTRIP:START -->" in text:
        hub_text = (ROOT / "this-week.html").read_text(encoding="utf-8")
        text = replace_block(
            text,
            "<!-- WEEKLY:HOMESTRIP:START -->",
            "<!-- WEEKLY:HOMESTRIP:END -->",
            render_strip(reviewed, carried_week_dates(hub_text, reviewed)),
            required=True,
        )
    first = payload["updates"][0]
    inner = f'''        <div class="card" style="padding: var(--space-xl);">
          <h2 style="font-size: 1.35rem; margin-bottom: var(--space-sm);">{esc(first["title"])}</h2>
          <p style="line-height: 1.75; margin-bottom: var(--space-md);">{esc(first["body"])}</p>
          <a href="this-week.html" class="btn btn-primary">Read the brief</a>
        </div>'''
    if "<!-- WEEKLY:HOME:START -->" in text:
        text = replace_block(text, "<!-- WEEKLY:HOME:START -->", "<!-- WEEKLY:HOME:END -->", inner)
    home.write_text(text, encoding="utf-8")


BLOG_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{desc}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://aicareertransition.com/blog/{slug}.html">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="https://aicareertransition.com/blog/{slug}.html">
  <meta property="og:image" content="https://aicareertransition.com/images/og-image.png">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="alternate" type="application/rss+xml" title="AI Career Transition — This Week in AI" href="/feed.xml">
  <script type="application/ld+json">
  {{"@context":"https://schema.org","@type":"BlogPosting","headline":"{title}","description":"{desc}","datePublished":"{date}","dateModified":"{date}","author":{{"@type":"Person","name":"AI Career Transition Editorial Team"}},"publisher":{{"@type":"Organization","name":"AI Career Transition","logo":{{"@type":"ImageObject","url":"https://aicareertransition.com/images/og-image.png"}}}},"image":"https://aicareertransition.com/images/og-image.png","mainEntityOfPage":{{"@type":"WebPage","@id":"https://aicareertransition.com/blog/{slug}.html"}}}}
  </script>
  <link rel="icon" type="image/svg+xml" href="../images/favicon.svg">
  <link rel="stylesheet" href="../css/styles.css?v={css_ver}">
  <title>{title} | AI Career Transition</title>
  <script>window.addEventListener("load",function(){{var e=document.createElement("script");e.src="/js/load-third-party.js";e.async=true;document.head.appendChild(e);}});</script>
</head>
<body>
  <a href="#main-content" class="skip-link">Skip to main content</a>
  <nav class="navbar" role="navigation" aria-label="Main navigation"><div class="navbar-container"><a href="/" class="navbar-logo" aria-label="AI Career Transition Home"><svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="36" height="36" rx="8" fill="url(#logo-gradient)"/><path d="M18 8L26 24H10L18 8Z" fill="white" fill-opacity="0.9"/><circle cx="18" cy="22" r="3" fill="white"/><defs><linearGradient id="logo-gradient" x1="0" y1="0" x2="36" y2="36"><stop stop-color="#2563eb"/><stop offset="1" stop-color="#1d4ed8"/></linearGradient></defs></svg><span>AI Career Transition</span></a><div class="navbar-menu"><a href="../this-week.html" class="navbar-link">This Week</a><a href="../101.html" class="navbar-link">Learn</a><a href="../prompts.html" class="navbar-link">Prompts</a><a href="../career.html" class="navbar-link">Career</a><a href="../use-cases.html" class="navbar-link">Use cases</a><a href="../blog.html" class="navbar-link active">Blog</a></div><div class="navbar-actions"><a href="../career.html" class="btn btn-primary">Start</a></div><button class="navbar-toggle" aria-label="Toggle navigation" aria-expanded="false"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg></button></div></nav>
  <main id="main-content"><article class="section" style="padding-top: 120px;"><div class="container" style="max-width: 760px;">
    <header style="margin-bottom: var(--space-2xl);">
      <p style="font-size:15px; color: var(--color-text-muted); margin-bottom: var(--space-md);"><a href="../this-week.html">This Week in AI</a> · Reviewed <time datetime="{date}">{date_human}</time></p>
      <h1 class="ax-h1 ax-h1--post" style="margin-bottom: var(--space-lg);">{title}</h1>
      <p style="font-size: 1.0625rem; line-height: 1.75; color: var(--color-text-secondary);">{desc}</p>
      <p class="proof-meta" style="margin-top: var(--space-md);">Official vendor sources only. This is a career brief, not a news dump and not a university catalog.</p>
    </header>
{body}
    <p style="margin-top: var(--space-xl);"><a href="../this-week.html" class="btn btn-primary">This Week in AI</a></p>
  </div></article></main>
  <footer class="footer"><div class="container"><div class="footer-bottom"><p>&copy; 2026 AI Career Transition. All rights reserved. · <a href="../privacy.html">Privacy</a> · <a href="../terms.html">Terms</a></p></div></div></footer>
  <script src="../js/main.js?v=20260928r2" defer></script>
</body>
</html>
'''


def write_post(post: dict, date: str, date_human: str) -> Path:
    out = ROOT / "blog" / f"{post['slug']}.html"
    html = BLOG_TEMPLATE.format(
        slug=post["slug"],
        title=esc(post["title"]),
        desc=esc(post["description"]),
        category=esc(post["category"]),
        date=date,
        date_human=date_human,
        body=post["body_html"],
        css_ver=CSS_VER,
    )
    out.write_text(html, encoding="utf-8")
    return out


def prepend_blog_card(post: dict, date: str, date_human: str) -> None:
    blog = ROOT / "blog.html"
    text = blog.read_text(encoding="utf-8")
    if f'blog/{post["slug"]}.html' in text:
        return
    card = f'''        <!-- Auto-generated weekly brief — {date} -->
        <article class="card" style="padding: var(--space-xl); margin-bottom: var(--space-lg);">
          <div style="display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-sm); flex-wrap: wrap;"><span class="prompt-card-category" style="margin: 0;">{esc(post["category"])}</span></div>
          <h3 style="margin-bottom: var(--space-sm); font-size: 1.25rem; line-height: 1.35;"><a href="blog/{post["slug"]}.html" style="color: var(--color-text-primary); text-decoration: none;">{esc(post["title"])}</a></h3>
          <p style="line-height: 1.7; color: var(--color-text-secondary); margin-bottom: var(--space-md);">{esc(post["description"])}</p>
          <a href="blog/{post["slug"]}.html" style="color: var(--color-accent-primary); font-weight: 600;">Read</a>
        </article>
'''
    anchor = '<h2 class="animate-on-scroll" style="margin-bottom: var(--space-xl); font-size: 1.375rem;">All Posts</h2>'
    if anchor in text:
        text = text.replace(anchor, anchor + "\n\n" + card, 1)
        blog.write_text(text, encoding="utf-8")


def update_llms(post: dict, date: str) -> None:
    path = ROOT / "llms.txt"
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"# Last updated: \d{4}-\d{2}-\d{2}", f"# Last updated: {date}", text)
    url = f"https://aicareertransition.com/blog/{post['slug']}.html"
    if url not in text:
        text = text.replace(
            "## Current AI Workflow Updates\n",
            f"## Current AI Workflow Updates\n- {url}\n",
            1,
        )
    path.write_text(text, encoding="utf-8")


def existing_slugs() -> list[str]:
    return [p.stem for p in (ROOT / "blog").glob("*.html")]


_HERO_DATE_BADGE = re.compile(
    r'\s*<div class="hero-badge"[^>]*>\s*(?:Updated|Published|Archived)[^<]*</div>',
    re.IGNORECASE,
)
_UPDATED_MONTH_LINE = re.compile(
    r'\s*<p style="font-size: 0.8125rem; color: var\(--color-text-muted\); margin-top: var\(--space-sm\);">Updated [A-Za-z]+ 20\d{2}</p>',
)
_LAST_UPDATED_HERO = re.compile(
    r'<p class="hero-description">Last updated: [^<]+</p>\s*',
)
_LISTING_TIME = re.compile(
    r'<span style="font-size: 0.8125rem; color: var\(--color-text-muted\);">'
    r'<time datetime="[^"]*">[^<]*</time>'
    r'(?:\s*·\s*([^<]+))?</span>',
)
_WEEK_OF_PREFIX = re.compile(
    r"Week of (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}:\s*",
)
_BYLINE_DATE = re.compile(
    r'(This Week in AI</a>)\s*·\s*[A-Z][a-z]+ \d{1,2}, \d{4}',
)


def strip_date_labels() -> None:
    """Remove visible calendar chips so pages do not look frozen. Keep JSON-LD/RSS dates."""
    for path in ROOT.rglob("*.html"):
        if any(part.startswith(".") for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        orig = text
        text = _HERO_DATE_BADGE.sub("", text)
        text = _UPDATED_MONTH_LINE.sub("", text)
        text = _LAST_UPDATED_HERO.sub("", text)
        text = _WEEK_OF_PREFIX.sub("", text)
        text = _BYLINE_DATE.sub(r"\1", text)

        def _listing(m: re.Match) -> str:
            extra = m.group(1)
            if extra:
                return (
                    f'<span style="font-size: 0.8125rem; color: var(--color-text-muted);">'
                    f"{extra}</span>"
                )
            return ""

        text = _LISTING_TIME.sub(_listing, text)
        text = text.replace(
            'Updated weekly · <time id="hub-updated"',
            'Updated weekly <time id="hub-updated"',
        )
        if text != orig:
            path.write_text(text, encoding="utf-8")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", type=Path, default=None)
    parser.add_argument("--date", default=None, help="ISO date for the brief slug (default: today)")
    args = parser.parse_args()

    today = datetime.datetime.now(_UTC).date()
    if args.date:
        today = datetime.date.fromisoformat(args.date)
    monday = today - datetime.timedelta(days=today.weekday())
    week_date = today.isoformat()
    week_label = "This week"
    week_slug = f"weekly-ai-brief-{week_date}"
    slugs = existing_slugs()

    payload = None
    if args.payload:
        payload = json.loads(args.payload.read_text(encoding="utf-8"))
        print(f"[info] using payload {args.payload}")
    elif os.environ.get("CURSOR_API_KEY"):
        raw = call_agent(build_prompt(week_label, week_date, slugs))
        if raw:
            try:
                payload = extract_json(raw)
                print("[info] using Cursor agent payload")
            except Exception as e:
                print(f"[warn] could not parse agent JSON: {e}", file=sys.stderr)

    if payload is None:
        updates = fetch_feed_updates(monday)
        print(f"[info] official feeds returned {len(updates)} item(s)")
        payload = payload_from_updates(updates, week_label, week_date)

    payload["week_date"] = week_date
    payload["week_label"] = week_label
    payload.setdefault("post", {})["slug"] = week_slug
    if not payload.get("prompt_of_week"):
        payload["prompt_of_week"] = AGENT_PROMPT_DEFAULT

    errs = validate(payload, slugs, week_slug)
    if errs:
        print(f"[fatal] validation failed ({len(errs)}):", file=sys.stderr)
        for e in errs:
            print(f"  x {e}", file=sys.stderr)
        return 1

    date_human = today.strftime("%B %-d, %Y")
    post = payload["post"]
    try:
        apply_hub_metadata(payload)
        rewrite_hub((ROOT / "this-week.html").read_text(encoding="utf-8"), payload)
    except HubRewriteError as err:
        print(f"[fatal] hub rewrite failed: {err}", file=sys.stderr)
        return 1
    # The live brief stays on this-week.html. A weekly slug is not a second
    # copy of the same week. The outgoing hub is archived inside update_hub.
    if post.get("slug") and post["slug"] != week_slug:
        write_post(post, week_date, date_human)
        prepend_blog_card(post, week_date, date_human)
        update_llms(post, week_date)
    try:
        update_hub(payload)
    except HubRewriteError as err:
        print(f"[fatal] hub rewrite failed: {err}", file=sys.stderr)
        return 1
    # Keep visible last-reviewed dates. Do not strip calendar labels.

    import build_sitemap
    build_sitemap.main()
    build_feed.main()

    print(f"[ok] published weekly brief {post['slug']} and refreshed hub for {week_label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
