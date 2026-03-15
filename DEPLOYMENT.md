# Deployment: Cursor → GitHub → GoDaddy (Go-Live)

**Automated:** Code from Cursor to GitHub (push from here).  
**Manual:** In cPanel, pull from GitHub and deploy to the live site.

---

## Your workflow

1. **Code in Cursor** — edit, save.
2. **Push to GitHub** (automated from your side):
   ```bash
   git add -A
   git commit -m "Your change description"
   git push origin main
   ```
3. **Deploy to live site** (manual in cPanel):
   - Go to **cPanel** → **Files** → **Git Version Control**.
   - Open your repo → **Pull or Deploy** tab.
   - Click **Update from Remote** (pulls latest from GitHub).
   - Click **Deploy HEAD Commit**.

Your live site updates after step 3. The repo on GitHub is always the source of truth; cPanel just pulls and deploys when you’re ready.

---

## One-time setup in GoDaddy cPanel

If you haven’t already connected the repo:

1. **Open cPanel**  
   GoDaddy → your hosting → **Manage** → **cPanel**.

2. **Git Version Control**  
   **Files** → **Git Version Control** → **Create** / **Clone a Repository**.

3. **Clone from GitHub**
   - **Repository URL:** `https://github.com/dfrm25/AIcareertransition.com.git`
   - **Branch:** `main`
   - **Repository path:** default (e.g. `repositories/AIcareertransition.com`) is fine.
   - **Deployment path:** `public_html` (or your web root).

4. **First deploy**  
   **Pull or Deploy** → **Update from Remote** → **Deploy HEAD Commit**.

---

## What `.cpanel.yml` does

When you click **Deploy HEAD Commit**, cPanel runs the tasks in `.cpanel.yml`:

- Syncs repo files into your deployment path (e.g. `public_html`), excluding `.git`, `.gitignore`, `.cpanel.yml`, `.DS_Store`.
- Sets directory permissions to `755` and file permissions to `644`.

If your site lives in a subdirectory (e.g. `public_html/aireer`), edit `.cpanel.yml` and set:

```yaml
- export DEPLOYPATH=${HOME}/public_html/aireer/
```

---

## Quick reference

| Step           | Where              | Action |
|----------------|--------------------|--------|
| Edit code      | Cursor             | Save files |
| Push to GitHub | Cursor / Terminal  | `git add -A && git commit -m "..." && git push origin main` |
| Pull on server | cPanel → Git → Pull or Deploy | **Update from Remote** |
| Go live        | cPanel → Git → Pull or Deploy | **Deploy HEAD Commit** |

Repo: [github.com/dfrm25/AIcareertransition.com](https://github.com/dfrm25/AIcareertransition.com)
