# Deployment — single package (Cursor → GitHub → cPanel)

Everything you ship is **one Git repository**. There is no separate “deployment bundle”: **push `main`**, then in cPanel **pull** and **Deploy HEAD Commit**. The server copies the repo into `public_html` per `.cpanel.yml`.

---

## Production deployment log (cPanel)

Record each go-live here so “last deployed” in cPanel always has a paper trail.

| Field | Value |
|--------|--------|
| **Last deployed (server)** | Mar 29, 2026 8:29:53 PM (cPanel) |
| **Commit SHA** | `b9a81470abf8f7d5f32ce8e17012186d2371621a` |
| **Author** | Design Forge (designforge.rm@gmail.com) |
| **Commit date** | Mar 29, 2026 9:11:40 AM |
| **Subject** | Blog: Microsoft Copilot model menu (screenshot) — better than Auto |

**On GitHub `main` (may be ahead of public_html):** pull the latest `main` (includes career hub, new blog posts, nav/sitemap, deployment docs). In cPanel: **Update from Remote**, then **Deploy HEAD Commit**, then refresh this table with the new “Last deployed” time and SHA from cPanel.

---

## End-to-end workflow

1. **Edit** in Cursor → save.
2. **Commit and push** to GitHub:
   ```bash
   git add -A
   git commit -m "Describe the change"
   git push origin main
   ```
3. **cPanel** → **Files** → **Git Version Control** → open this repo → **Pull or Deploy**:
   - **Update from Remote**
   - **Deploy HEAD Commit**

Live site updates after step 3. **GitHub `main` is the source of truth.**

Repo: [github.com/dfrm25/AIcareertransition.com](https://github.com/dfrm25/AIcareertransition.com)

---

## What `.cpanel.yml` does

On **Deploy HEAD Commit**, cPanel runs:

- `rsync` from the clone into `${HOME}/public_html/` (see `.cpanel.yml` for exact flags).
- Excludes: `.git`, `.cpanel.yml`, `.gitignore`, `.DS_Store`.
- Sets directories **755**, files **644**.

If the site lives in a subdirectory, edit `DEPLOYPATH` in `.cpanel.yml`.

---

## Verify files on the server

Use **`DEPLOY_MANIFEST.txt`** in this repo as the checklist of HTML/CSS/JS/images and key root files that should appear under `public_html` after deploy.

---

## Legacy docs (FTP era)

These are **not** the primary process anymore; Git deploy replaces manual file lists.

| File | Purpose |
|------|--------|
| `FILES_TO_UPLOAD.txt` | Deprecated list; see `DEPLOY_MANIFEST.txt` |
| `UPLOAD_CHECKLIST.md` | Old step-by-step FTP checklist |
| `GODADDY_*.md` | Historical GoDaddy notes |

---

## One-time cPanel Git setup

1. **cPanel** → **Git Version Control** → **Clone**.
2. **Repository URL:** `https://github.com/dfrm25/AIcareertransition.com.git`
3. **Branch:** `main`
4. **Deployment path:** `public_html` (or your web root).
5. **Pull or Deploy** → **Update from Remote** → **Deploy HEAD Commit**.

---

## Quick reference

| Step | Where | Action |
|------|--------|--------|
| Edit | Cursor | Save |
| Publish to GitHub | Terminal | `git add -A && git commit -m "…" && git push origin main` |
| Pull on server | cPanel → Git | **Update from Remote** |
| Go live | cPanel → Git | **Deploy HEAD Commit** |

Optional: run `scripts/package-deployment.sh` from the repo root to build a local zip (backup or manual upload); normal go-live is still Git + cPanel.
