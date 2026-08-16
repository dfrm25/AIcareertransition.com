# Hands-off weekly updates (no cPanel)

cPanel Git does **not** go live when GitHub `main` changes. You still have to click **Update from Remote** and **Deploy HEAD Commit** unless GitHub deploys over FTPS.

After the three FTP secrets below are set, you can ignore cPanel for weekly briefs and for normal pushes to `main`.

## What runs unattended

Every Monday at 14:00 UTC, GitHub Actions:

1. Pulls recent posts from official OpenAI, Google, and Microsoft feeds
2. Writes a new This Week brief, refreshes the hub and homepage card
3. Runs guardrails (stale model names, dead links, invalid XML)
4. Commits to `main`
5. Uploads the site to `public_html/` over FTPS

Pushes you make to `main` (from Cursor or git) also deploy over FTPS.

This does **not** rewrite the whole site each week. Learn, Prompts, and Career stay as shipped. Only This Week, the homepage card, the blog brief, `feed.xml`, and `sitemap.xml` refresh.

No Cursor API key is required. If you add `CURSOR_API_KEY`, the agent can rewrite the weekly copy. If feeds are quiet that week, a conservative fallback still refreshes the date so the hub never goes stale.

## One-time setup (required to skip cPanel)

1. In GoDaddy cPanel → **FTP Accounts**, copy the FTP hostname, username, and password.
2. In GitHub → this repo → **Settings → Secrets and variables → Actions**, add:

| Secret | Value |
| --- | --- |
| `FTP_SERVER` | FTP hostname (often `ftp.aicareertransition.com` or the server host) |
| `FTP_USERNAME` | FTP username |
| `FTP_PASSWORD` | FTP password |

3. Test once: **Actions → Deploy live site → Run workflow**. Confirm [aicareertransition.com](https://aicareertransition.com) updated. After that, stop using the cPanel Git buttons.

**Optional:** `CURSOR_API_KEY` from [Cursor Dashboard → Integrations](https://cursor.com/dashboard/integrations).

## Rollback

```bash
git revert HEAD
git push origin main
```
