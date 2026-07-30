#!/usr/bin/env python3
"""Weekly content generator — runs unattended in CI via the Cursor SDK.

Flow (fail-closed): ask a Cursor agent for a STRICT JSON payload describing this
week's AI updates + one new blog post, validate every field HARD (official
source domains, no deprecated model names, safe slug, working internal links),
and only THEN render deterministic HTML into fixed templates and marker blocks.
If anything is missing or invalid, it writes nothing and exits non-zero so the
workflow skips the deploy. No half-baked content ever reaches the site.

Env:
  CURSOR_API_KEY   required (Cursor Dashboard -> Integrations)
  WEEKLY_MODEL     optional model id (default: composer-2.5)

Usage:
  python3 scripts/generate_weekly.py
"""
from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_feed  # noqa: E402  (local helper, reused for post extraction)

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

CATEGORY_COLORS = {
    "Models": "#7c3aed", "Agents": "#10b981", "Tools": "#2563eb",
    "Governance": "#b45309", "Multimodal": "#0284c7", "Connected AI": "#0891b2",
}


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
- Emphasize durable workflow skills and concrete career actions over hype.
- Keep everything factual and conservative; if unsure about a claim, describe the capability generally and link the official docs.
- The post.body_html must NOT include <html>, <head>, <nav>, or <footer> — body content only.

Existing post slugs (do not reuse): {", ".join(existing_slugs[:40])}
"""


def call_agent(prompt: str) -> str:
    try:
        import os
        from cursor_sdk import Agent, AgentOptions, LocalAgentOptions
    except Exception as e:  # pragma: no cover - import/runtime env issue
        print(f"[fatal] cursor-sdk not importable: {e}", file=sys.stderr)
        raise SystemExit(1)

    api_key = os.environ.get("CURSOR_API_KEY")
    if not api_key:
        print("[fatal] CURSOR_API_KEY not set", file=sys.stderr)
        raise SystemExit(1)
    model = os.environ.get("WEEKLY_MODEL", "composer-2.5")

    from cursor_sdk import CursorAgentError
    try:
        result = Agent.prompt(
            prompt,
            AgentOptions(
                api_key=api_key,
                model=model,
                local=LocalAgentOptions(cwd=str(ROOT)),
            ),
        )
    except CursorAgentError as err:  # run never started
        print(f"[fatal] agent startup failed: {err} retryable={getattr(err,'is_retryable',None)}", file=sys.stderr)
        raise SystemExit(1)

    if getattr(result, "status", None) == "error":  # ran but failed
        print(f"[fatal] agent run failed: {getattr(result,'id','?')}", file=sys.stderr)
        raise SystemExit(2)

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
def _domain_ok(url: str) -> bool:
    return url.startswith("https://") and any(
        (f"//{d}" in url or f".{d}" in url) for d in OFFICIAL_DOMAINS
    )


def validate(payload: dict, existing_slugs: list[str]) -> list[str]:
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
    if slug in existing_slugs:
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
        color = CATEGORY_COLORS.get(u["category"], "#2563eb")
        internal = u["action_link"]
        out.append(
            f'''        <article class="card" style="padding: var(--space-xl); border-left: 4px solid {color}; margin-bottom: var(--space-lg);">
          <div style="display:flex;align-items:center;gap:var(--space-sm);margin-bottom:var(--space-sm);flex-wrap:wrap;">
            <span class="prompt-card-category" style="margin:0;">{esc(u["category"])}</span>
            <span style="font-size:0.8125rem;color:var(--color-text-muted);">Official source</span>
          </div>
          <h3 style="margin-bottom:var(--space-sm);font-size:1.15rem;line-height:1.4;">{esc(u["title"])}</h3>
          <p style="line-height:1.75;color:var(--color-text-secondary);margin-bottom:var(--space-md);">{esc(u["body"])} <a href="{esc(u["source_url"])}" target="_blank" rel="noopener noreferrer" style="color:var(--color-accent-primary);">Source →</a></p>
          <p style="line-height:1.75;font-size:0.95rem;"><strong>Career action:</strong> {esc(u["action"])} <a href="{esc(internal)}" style="color:var(--color-accent-primary);">Go →</a></p>
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
            f'''          <article class="card" style="padding: var(--space-lg); border-left: 4px solid #7c3aed; margin-bottom: var(--space-md);">
            <span style="font-size:0.8125rem;color:var(--color-text-muted);"><time datetime="{post["date"]:%Y-%m-%d}">{post["date"]:%B %-d, %Y}</time></span>
            <h3 style="margin:6px 0;font-size:1.1rem;"><a href="{esc(rel)}" style="color:var(--color-text-primary);text-decoration:none;">{esc(post["title"])}</a></h3>
            <a href="{esc(rel)}" style="color:var(--color-accent-primary);font-weight:600;font-size:0.9rem;">Read →</a>
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
  <link rel="stylesheet" href="../css/styles.css">
  <title>{title} | AI Career Transition</title>
  <script>window.addEventListener("load",function(){{var e=document.createElement("script");e.src="/js/load-third-party.js";e.async=true;document.head.appendChild(e);}});</script>
</head>
<body>
  <a href="#main-content" class="skip-link">Skip to main content</a>
  <nav class="navbar" role="navigation" aria-label="Main navigation"><div class="navbar-container"><a href="../index.html" class="navbar-logo" aria-label="AI Career Transition Home"><svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="36" height="36" rx="8" fill="url(#logo-gradient)"/><path d="M18 8L26 24H10L18 8Z" fill="white" fill-opacity="0.9"/><circle cx="18" cy="22" r="3" fill="white"/><defs><linearGradient id="logo-gradient" x1="0" y1="0" x2="36" y2="36"><stop stop-color="#2563eb"/><stop offset="1" stop-color="#1d4ed8"/></linearGradient></defs></svg><span>AI Career Transition</span></a><div class="navbar-menu"><a href="../index.html" class="navbar-link">Home</a><a href="../this-week.html" class="navbar-link">This Week</a><a href="../101.html" class="navbar-link">AI 101</a><a href="../201.html" class="navbar-link">AI 201</a><a href="../prompts.html" class="navbar-link">Prompt Library</a><a href="../career.html" class="navbar-link">Career</a><a href="../artifacts.html" class="navbar-link">Artifacts</a><a href="../blog.html" class="navbar-link active">Blog</a><a href="../tools-comparison.html" class="navbar-link">Compare Tools</a></div><div class="navbar-actions"><a href="../index.html#quiz" class="btn btn-primary">Take Quiz</a></div><button class="navbar-toggle" aria-label="Toggle navigation" aria-expanded="false"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg></button></div></nav>
  <main id="main-content"><article class="section" style="padding-top: 120px;"><div class="container" style="max-width: 860px;">
    <header style="margin-bottom: var(--space-2xl);">
      <p style="font-size: 0.8125rem; color: var(--color-text-muted); margin-bottom: var(--space-sm);"><a href="../this-week.html" style="color: var(--color-accent-primary);">This Week in AI</a> / {category}</p>
      <div class="hero-badge" style="margin-bottom: var(--space-md);">Published {date_human}</div>
      <h1 style="font-size: clamp(1.9rem, 4vw, 2.6rem); line-height: 1.2; margin-bottom: var(--space-lg);">{title}</h1>
      <p style="font-size: 1.0625rem; line-height: 1.8; color: var(--color-text-secondary);">{desc}</p>
      <p style="font-size:0.9rem; color:var(--color-text-muted); margin-top:var(--space-md);">Reviewed by the AI Career Transition editorial team. We prioritize official product docs and source links over hype. Model and product names change fast; the workflow patterns are the durable skill.</p>
    </header>
{body}
    <div class="card" style="padding: var(--space-xl); margin-top: var(--space-2xl); background: linear-gradient(145deg, rgba(37,99,235,0.06) 0%, rgba(16,185,129,0.06) 100%);">
      <h2 style="font-size:1.2rem;margin-bottom:var(--space-sm);">Keep up every week</h2>
      <p style="line-height:1.8;margin-bottom:var(--space-md);">This brief is part of <a href="../this-week.html" style="color:var(--color-accent-primary);">This Week in AI</a> — updated every week. <a href="/feed.xml" style="color:var(--color-accent-primary);">Subscribe via RSS</a> or get the email digest on the hub.</p>
      <a href="../this-week.html" class="btn btn-primary">Go to This Week in AI</a>
    </div>
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
    )
    out.write_text(html, encoding="utf-8")
    return out


def prepend_blog_card(post: dict, date: str, date_human: str) -> None:
    blog = ROOT / "blog.html"
    text = blog.read_text(encoding="utf-8")
    card = f'''        <!-- Auto-generated weekly brief — {date} -->
        <article class="card animate-on-scroll" style="padding: var(--space-xl); border-left: 4px solid #2563eb; margin-bottom: var(--space-lg);">
          <div style="display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-sm); flex-wrap: wrap;"><span class="prompt-card-category" style="margin: 0; background: rgba(37,99,235,0.1); color: #1d4ed8; border-color: rgba(37,99,235,0.2);">{esc(post["category"])}</span><span style="font-size: 0.8125rem; color: var(--color-text-muted);"><time datetime="{date}">{date_human}</time></span></div>
          <h3 style="margin-bottom: var(--space-sm); font-size: 1.25rem; line-height: 1.35;"><a href="blog/{post["slug"]}.html" style="color: var(--color-text-primary); text-decoration: none;">{esc(post["title"])}</a></h3>
          <p style="line-height: 1.7; color: var(--color-text-secondary); margin-bottom: var(--space-md);">{esc(post["description"])}</p>
          <a href="blog/{post["slug"]}.html" style="color: var(--color-accent-primary); font-weight: 600; font-size: 0.9375rem;">Read full post -></a>
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
    slugs = existing_slugs()

    prompt = build_prompt(week_label, week_date, slugs)
    raw = call_agent(prompt)

    try:
        payload = extract_json(raw)
    except Exception as e:
        print(f"[fatal] could not parse agent JSON: {e}", file=sys.stderr)
        print("---agent output start---\n" + raw[:2000] + "\n---end---", file=sys.stderr)
        return 1

    # Force canonical dates/slug regardless of what the model echoed.
    payload["week_date"] = week_date
    payload["week_label"] = week_label
    payload.setdefault("post", {})["slug"] = f"weekly-ai-brief-{week_date}"

    errs = validate(payload, slugs)
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

    # Regenerate machine files.
    import build_sitemap
    build_sitemap.main()
    build_feed.main()

    print(f"[ok] published weekly brief {post['slug']} and refreshed hub for {week_label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
