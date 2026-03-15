# Deployment: Cursor → GitHub → GoDaddy (Go-Live)

This doc describes how to get code from this repo live on your GoDaddy-hosted site using Git and cPanel.

---

## End-to-end flow

1. **Code** in Cursor (edit, save).
2. **Commit & push** to GitHub:
   ```bash
   git add -A
   git commit -m "Your change description"
   git push origin main
   ```
3. **Deploy to website** using one of the options below.

---

## One-time setup in GoDaddy cPanel

### 1. Open cPanel

- Go to [GoDaddy](https://www.godaddy.com) → your product → **Manage** (hosting).
- Open **cPanel** (or “Hosting” then cPanel).

### 2. Git Version Control

- In cPanel, go to **Files** → **Git Version Control** (or **Git™ Version Control**).
- Click **Create** (or **Clone a Repository**).

### 3. Clone from GitHub

- **Repository URL:** `https://github.com/dfrm25/AIcareertransition.com.git`  
  (or SSH: `git@github.com:dfrm25/AIcareertransition.com.git` if your host supports it)
- **Branch:** `main`
- **Repository path:** Leave default (e.g. `repositories/AIcareertransition.com`) or choose a folder name.
- **Deployment path:** Set to your web root, e.g. `public_html` (so the site is at your domain root).
- Create/Clone the repo. cPanel will pull from GitHub.

### 4. First deploy

- In Git Version Control, open your repo → **Pull or Deploy** tab.
- Click **Update from Remote** (pulls latest from GitHub).
- Click **Deploy HEAD Commit**.

The `.cpanel.yml` in this repo will run and copy all site files into `public_html` (or whatever path you set), with correct permissions.

---

## How you deploy after each change

### Option A: Manual (pull then deploy)

After you push from Cursor to GitHub:

1. In cPanel → **Git Version Control** → your repo → **Pull or Deploy**.
2. Click **Update from Remote** (pull from GitHub).
3. Click **Deploy HEAD Commit**.

Your live site updates after step 3.

### Option B: Automatic (push to cPanel)

If your host gives you a **cPanel Git repository URL** (a repo that lives on the server, not GitHub), you can push to both GitHub and cPanel so that a single push to cPanel triggers deploy:

1. In Cursor (or terminal), add cPanel as a second remote (replace with the URL cPanel shows you):
   ```bash
   git remote add cpanel https://your-domain.com:2083/cpsess.../git/branch/main/your-repo.git
   ```
   Or use the exact URL from cPanel’s “Clone” / “Repository URL” for the repo **on the server**.

2. After pushing to GitHub, also push to cPanel:
   ```bash
   git push origin main    # backup / collaboration
   git push cpanel main   # triggers deploy on server
   ```

Then your workflow is: **code in Cursor → commit → push to GitHub + push to cpanel → site updates automatically** (no “Update from Remote” or “Deploy HEAD” in the UI).

---

## What `.cpanel.yml` does

- Runs when you click **Deploy HEAD Commit** (and when you push to a cPanel-managed repo, if you use Option B).
- Syncs the repo into your deployment path (`$HOME/public_html/` by default), excluding `.git`, `.gitignore`, `.cpanel.yml`, and `.DS_Store`.
- Sets directory permissions to `755` and file permissions to `644`.

If your site lives in a subdirectory (e.g. `public_html/aireer`), change the `DEPLOYPATH` in `.cpanel.yml` to match, e.g.:

```yaml
- export DEPLOYPATH=${HOME}/public_html/aireer/
```

---

## Quick reference

| Step              | Where        | Action |
|-------------------|-------------|--------|
| Edit code         | Cursor      | Save files |
| Commit & push     | Terminal / Cursor | `git add -A && git commit -m "..." && git push origin main` |
| Pull latest       | cPanel → Git → Pull or Deploy | **Update from Remote** |
| Go live           | cPanel → Git → Pull or Deploy | **Deploy HEAD Commit** |

Repo: [github.com/dfrm25/AIcareertransition.com](https://github.com/dfrm25/AIcareertransition.com)
