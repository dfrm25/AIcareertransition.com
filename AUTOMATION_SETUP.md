# Weekly auto-update

Every Monday at 14:00 UTC, GitHub Actions:

1. Pulls recent posts from official OpenAI, Google, and Microsoft feeds
2. Writes a new This Week brief, refreshes the hub and homepage card
3. Runs guardrails (stale model names, dead links, invalid XML)
4. Commits to `main`
5. Deploys over FTPS if `FTP_SERVER` is set

No Cursor API key is required. If you add `CURSOR_API_KEY`, the agent can rewrite the copy. If feeds are quiet that week, a conservative fallback still refreshes the date so the site never goes stale.

## One-time setup

GitHub → repo → **Settings → Secrets and variables → Actions**.

**Required for live deploy:**

| Secret | Value |
| --- | --- |
| `FTP_SERVER` | FTP host from GoDaddy cPanel |
| `FTP_USERNAME` | FTP username |
| `FTP_PASSWORD` | FTP password |

If you already pull from GitHub in cPanel, the commit to `main` is enough. FTP is optional.

**Optional:** `CURSOR_API_KEY` from [Cursor Dashboard → Integrations](https://cursor.com/dashboard/integrations).

Test once: **Actions → Weekly AI content update + deploy → Run workflow**.

## Rollback

```bash
git revert HEAD
git push origin main
```
