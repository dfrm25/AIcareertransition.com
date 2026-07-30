# Weekly Auto-Update + Auto-Deploy — One-Time Setup

This repo now updates itself **every week with no human involved**: a GitHub
Action writes a new "This Week in AI" brief + refreshes the hub, runs automated
quality checks, and deploys to GoDaddy over FTPS. You only have to do the
**one-time credential setup below** (GitHub won't let anyone — including
automation — create your secrets for you). After that, it runs untouched.

## What runs, and when

- **Schedule:** every Monday 14:00 UTC (`.github/workflows/weekly-update.yml`).
- **Pipeline:** generate content (Cursor SDK) → guardrails (block bad content)
  → commit to `main` → deploy site to GoDaddy `public_html` via FTPS.
- **Fail-closed:** if the generated content is missing, invalid, cites a
  non-official source, contains a stale/deprecated model name, or breaks an
  internal link, the run **fails and nothing is deployed**. The live site is
  never touched by a bad run.

## One-time setup (~10 minutes)

### 1. Add the Cursor API key

1. Go to [Cursor Dashboard → Integrations](https://cursor.com/dashboard/integrations) and create an **API key**.
2. In GitHub: repo → **Settings → Secrets and variables → Actions → New repository secret**.
3. Name: `CURSOR_API_KEY` — value: the key you copied.

### 2. Add your GoDaddy FTP credentials

Find these in **GoDaddy cPanel → Files → FTP Accounts** (use your main FTP
account, or create a dedicated one scoped to `public_html`).

Add three repository secrets (same Actions secrets screen):

| Secret name    | Value                                                        |
| -------------- | ------------------------------------------------------------ |
| `FTP_SERVER`   | Your FTP host, e.g. `ftp.aicareertransition.com` (or the server/IP cPanel shows) |
| `FTP_USERNAME` | Full FTP username, e.g. `deploy@aicareertransition.com`      |
| `FTP_PASSWORD` | The FTP account password                                     |

> The workflow uses **FTPS** (encrypted). If your host only offers plain FTP,
> change `protocol: ftps` to `protocol: ftp` in the workflow (less secure).
> The deploy targets `public_html/`. If your web root differs, edit
> `server-dir:` in the workflow.

### 3. Test it once (recommended)

1. Repo → **Actions → "Weekly AI content update + deploy" → Run workflow**.
2. Watch the run. On success you'll see a new commit
   `chore(content): weekly AI update YYYY-MM-DD` and the site updated live.
3. If the **Generate** or **Guardrails** step fails, nothing deploys — open the
   log to see exactly which check blocked it.

That's it. From now on it runs every Monday on its own.

## Tuning (optional)

- **Change the day/time:** edit the `cron` in the workflow. Format is
  `minute hour day-of-month month day-of-week` (UTC). `0 14 * * 1` = Mondays 14:00 UTC.
- **Change the model:** set a repository **variable** `WEEKLY_MODEL`
  (Settings → Variables → Actions). Defaults to `composer-2.5`.
- **Publish more/less often:** duplicate the cron line or change the day.

## How quality is protected without a human reviewer

`scripts/guardrails.py` runs on every generated update and hard-fails the deploy if it finds:

- a deprecated/retired model name (e.g. old Gemini/GPT/Claude versions),
- a source link that isn't on an official vendor domain (OpenAI, Google,
  Anthropic, Microsoft),
- a broken internal link,
- invalid `sitemap.xml` / `feed.xml`,
- a missing update marker in `this-week.html`.

The generator (`scripts/generate_weekly.py`) also validates the agent's JSON
before writing anything, so a bad model response results in **no file changes**.

## Rollback

Every weekly change is a normal git commit. To undo the latest one:

```bash
git revert HEAD
git push origin main
```

Then re-run the deploy (Actions → Run workflow) or deploy the reverted commit
from cPanel. You can also always deploy manually from cPanel's
"Deploy HEAD Commit" as before — the FTPS path and the cPanel path can coexist.

## Files involved

| File | Role |
| ---- | ---- |
| `.github/workflows/weekly-update.yml` | The scheduled pipeline |
| `scripts/generate_weekly.py`          | Generates + validates weekly content |
| `scripts/guardrails.py`               | Quality gate (blocks bad deploys) |
| `scripts/build_feed.py`               | Regenerates `feed.xml` (RSS) |
| `scripts/build_sitemap.py`            | Regenerates `sitemap.xml` |
| `this-week.html`                      | The weekly hub (has `<!-- WEEKLY:* -->` markers) |
| `requirements-automation.txt`         | Python deps for CI only |
