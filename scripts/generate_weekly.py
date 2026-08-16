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
)
DEPRECATED_RE = re.compile(
    r"gemini\s*2\.0\s*flash|gemini\s*1\.5|gemini\s*1\.0|\bgpt-3\.5\b|\bgpt-3\b|"
    r"text-davinci|\bclaude\s*2\b|\bclaude\s*instant\b|\bgoogle\s+bard\b|"
    r"\bbard\b(?!\w)|\bo1-preview\b|\bgpt-4\.0\b",
    re.IGNORECASE,
)
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
UPDATE_BORDER = "var(--color-border)"
CSS_VER = "20260816"

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
                }
            )
            if len(picked) >= 4:
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
    desc = f"{week_label}: what shipped from OpenAI, Anthropic, Google, and Microsoft, and one thing to do with it."
    return {
        "week_label": week_label,
        "week_date": week_date,
        "updates": updates[:4],
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
  "post": {{
    "slug": "weekly-ai-brief-{week_date}",
    "title": "blog post title, <= 90 chars",
    "description": "meta description, 1 sentence, <= 160 chars",
    "category": "Weekly Brief",
    "body_html": "valid inner HTML for the article body: 3-5 <section> blocks each with an <h2> and <p> paragraphs, using <a href=... target=_blank rel=noopener noreferrer> for official links"
  }}
}}

HARD RULES (violating any means your output is rejected):
- 2 to 4 updates. Each source_url MUST be on one of these official domains ONLY: {", ".join(OFFICIAL_DOMAINS)}.
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
    if not isinstance(updates, list) or not (2 <= len(updates) <= 4):
        errs.append("updates must be a list of 2-4 items")
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
    return errs


# --------------------------------------------------------------------------- #
# 3. Render into templates + marker blocks (only after validation passes)
# --------------------------------------------------------------------------- #
def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_updates(updates: list[dict]) -> str:
    out = []
    for u in updates:
        internal = u["action_link"]
        out.append(
            f'''        <article class="card" style="padding: var(--space-xl); margin-bottom: var(--space-lg);">
          <h3 style="margin-bottom:var(--space-sm);font-size:1.15rem;line-height:1.4;">{esc(u["title"])}</h3>
          <p style="line-height:1.75;color:var(--color-text-secondary);margin-bottom:var(--space-md);">{esc(u["body"])} <a href="{esc(u["source_url"])}" target="_blank" rel="noopener noreferrer">Source</a></p>
          <p style="line-height:1.75;font-size:0.95rem;"><strong>Do this:</strong> {esc(u["action"])} <a href="{esc(internal)}">Go</a></p>
        </article>'''
        )
    return "\n".join(out)


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
            <span style="font-size:0.8125rem;color:var(--color-text-muted);"><time datetime="{post["date"]:%Y-%m-%d}">{post["date"]:%B %-d, %Y}</time></span>
            <h3 style="margin:6px 0;font-size:1.1rem;"><a href="{esc(rel)}" style="color:var(--color-text-primary);text-decoration:none;">{esc(post["title"])}</a></h3>
            <a href="{esc(rel)}" style="color:var(--color-accent-primary);font-weight:600;font-size:0.9rem;">Read</a>
          </article>'''
        )
    return "\n".join(out)


def replace_block(text: str, start: str, end: str, new_inner: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    return pattern.sub(f"{start}\n{new_inner}\n        {end}", text, count=1)


def update_hub(payload: dict) -> None:
    hub = ROOT / "this-week.html"
    text = hub.read_text(encoding="utf-8")
    wd = payload["week_date"]
    label = payload["week_label"]
    text = re.sub(
        r'<time id="hub-updated" datetime="[^"]*"><!-- WEEKLY:DATE -->[^<]*</time>',
        f'<time id="hub-updated" datetime="{wd}"><!-- WEEKLY:DATE -->{esc(label)}</time>',
        text,
    )
    text = replace_block(
        text, "<!-- WEEKLY:UPDATES:START -->", "<!-- WEEKLY:UPDATES:END -->",
        render_updates(payload["updates"]),
    )
    text = replace_block(
        text, "<!-- WEEKLY:LATEST:START -->", "<!-- WEEKLY:LATEST:END -->",
        render_latest(),
    )
    prompt_html = (
        f'          <p style="line-height:1.8;color:var(--color-text-secondary);'
        f'font-family:var(--font-mono, monospace);font-size:0.95rem;">'
        f'"{esc(payload["prompt_of_week"])}"</p>'
    )
    text = replace_block(
        text, "<!-- WEEKLY:PROMPT:START -->", "<!-- WEEKLY:PROMPT:END -->", prompt_html
    )
    hub.write_text(text, encoding="utf-8")
    update_home(payload)


def update_home(payload: dict) -> None:
    home = ROOT / "index.html"
    if not home.exists():
        return
    first = payload["updates"][0]
    inner = f'''        <div class="card" style="padding: var(--space-xl);">
          <p style="font-size: 0.875rem; color: var(--color-text-muted); margin-bottom: var(--space-sm);">{esc(payload["week_label"])}</p>
          <h2 style="font-size: 1.35rem; margin-bottom: var(--space-sm);">{esc(first["title"])}</h2>
          <p style="line-height: 1.75; margin-bottom: var(--space-md);">{esc(first["body"])}</p>
          <a href="this-week.html" class="btn btn-primary">Read the brief</a>
        </div>'''
    text = home.read_text(encoding="utf-8")
    if "<!-- WEEKLY:HOME:START -->" in text:
        home.write_text(
            replace_block(text, "<!-- WEEKLY:HOME:START -->", "<!-- WEEKLY:HOME:END -->", inner),
            encoding="utf-8",
        )


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
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preload" href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" as="style" onload="this.onload=null;this.rel='stylesheet'">
  <noscript><link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet"></noscript>
  <link rel="stylesheet" href="../css/styles.css?v={css_ver}">
  <title>{title} | AI Career Transition</title>
  <script>window.addEventListener("load",function(){{var e=document.createElement("script");e.src="/js/load-third-party.js";e.async=true;document.head.appendChild(e);}});</script>
</head>
<body>
  <a href="#main-content" class="skip-link">Skip to main content</a>
  <nav class="navbar" role="navigation" aria-label="Main navigation"><div class="navbar-container"><a href="../index.html" class="navbar-logo" aria-label="AI Career Transition Home"><svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="36" height="36" rx="8" fill="url(#logo-gradient)"/><path d="M18 8L26 24H10L18 8Z" fill="white" fill-opacity="0.9"/><circle cx="18" cy="22" r="3" fill="white"/><defs><linearGradient id="logo-gradient" x1="0" y1="0" x2="36" y2="36"><stop stop-color="#2563eb"/><stop offset="1" stop-color="#1d4ed8"/></linearGradient></defs></svg><span>AI Career Transition</span></a><div class="navbar-menu"><a href="../this-week.html" class="navbar-link">This Week</a><a href="../101.html" class="navbar-link">Learn</a><a href="../prompts.html" class="navbar-link">Prompts</a><a href="../career.html" class="navbar-link">Career</a><a href="../blog.html" class="navbar-link active">Blog</a></div><div class="navbar-actions"><a href="../career.html" class="btn btn-primary">Start</a></div><button class="navbar-toggle" aria-label="Toggle navigation" aria-expanded="false"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg></button></div></nav>
  <main id="main-content"><article class="section" style="padding-top: 120px;"><div class="container" style="max-width: 760px;">
    <header style="margin-bottom: var(--space-2xl);">
      <p style="font-size: 0.875rem; color: var(--color-text-muted); margin-bottom: var(--space-md);"><a href="../this-week.html">This Week in AI</a> · {date_human}</p>
      <h1 style="font-size: clamp(1.75rem, 4vw, 2.4rem); line-height: 1.2; margin-bottom: var(--space-lg);">{title}</h1>
      <p style="font-size: 1.0625rem; line-height: 1.75; color: var(--color-text-secondary);">{desc}</p>
    </header>
{body}
    <p style="margin-top: var(--space-xl);"><a href="../this-week.html" class="btn btn-primary">This Week in AI</a></p>
  </div></article></main>
  <footer class="footer"><div class="container"><div class="footer-bottom"><p>&copy; 2026 AI Career Transition. All rights reserved. · <a href="../privacy.html">Privacy</a> · <a href="../terms.html">Terms</a></p></div></div></footer>
  <script src="../js/main.js" defer></script>
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
          <div style="display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-sm); flex-wrap: wrap;"><span class="prompt-card-category" style="margin: 0;">{esc(post["category"])}</span><span style="font-size: 0.8125rem; color: var(--color-text-muted);"><time datetime="{date}">{date_human}</time></span></div>
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


def main() -> int:
    today = datetime.datetime.now(_UTC).date()
    monday = today - datetime.timedelta(days=today.weekday())
    week_date = monday.isoformat()
    week_label = f"Week of {monday.strftime('%B %-d, %Y')}"
    week_slug = f"weekly-ai-brief-{week_date}"
    slugs = existing_slugs()

    payload = None
    if os.environ.get("CURSOR_API_KEY"):
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

    date_human = monday.strftime("%B %-d, %Y")
    post = payload["post"]
    write_post(post, week_date, date_human)
    prepend_blog_card(post, week_date, date_human)
    update_hub(payload)
    update_llms(post, week_date)

    import build_sitemap
    build_sitemap.main()
    build_feed.main()

    print(f"[ok] published weekly brief {post['slug']} and refreshed hub for {week_label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
