# Deployment — single package (Cursor → GitHub → cPanel)

Everything you ship is **one Git repository**. There is no separate “deployment bundle”: **push `main`**, then in cPanel **pull** and **Deploy HEAD Commit**. The server copies the repo into `public_html` per `.cpanel.yml`.

---

## Production deployment log (cPanel)

Record each go-live here so “last deployed” in cPanel always has a paper trail.

| Field | Value |
|--------|--------|
| **Last deployed (server)** | Mar 29, 2026 8:33:21 PM (cPanel) |
| **Commit SHA** | `9608c5ab1f63c931405bad7bf87ddde93660f863` |
| **Author** | Design Forge (designforge.rm@gmail.com) |
| **Commit date** | Mar 29, 2026 8:32:06 PM |
| **Subject** | DEPLOYMENT.md: avoid pinning stale SHA for pending deploy |

**Note:** This SHA is current `main` and includes the career hub, new blog posts, site-wide nav/sitemap updates, and deployment packaging docs. After each future go-live, replace the rows above using **Last Deployment Information** from cPanel.

---

## End-to-end workflow

1. **Edit** in Cursor → save.
2. **Regenerate the sitemap** (includes new or renamed HTML): from the repo root run `python3 scripts/build_sitemap.py` so `sitemap.xml` stays in sync before you commit.
3. **Commit and push** to GitHub:
   ```bash
   git add -A
   git commit -m "Describe the change"
   git push origin main
   ```
4. **cPanel** → **Files** → **Git Version Control** → open this repo → **Pull or Deploy**:
   - **Update from Remote**
   - **Deploy HEAD Commit**

Live site updates after deploy. **GitHub `main` is the source of truth.**

Repo: [github.com/dfrm25/AIcareertransition.com](https://github.com/dfrm25/AIcareertransition.com)

---

## Performance (PageSpeed / Lighthouse)

- **`.htaccess`** — enables compression and `Cache-Control` for `css`, `js`, images, and short revalidation for `html` (Apache must allow `mod_headers` / `mod_expires` / `mod_deflate`; most cPanel hosts do).
- **Third-party scripts** — GA4 and AdSense load **after** `window.load` via `/js/load-third-party.js` so they do not compete with first paint.
- **Fonts** — Google Fonts CSS is loaded with `rel="preload" … as="style"` then applied on `onload` (non-blocking), with `<noscript>` fallback.
- **Site JS** — `main.js` uses **`defer`** at the end of `<body>`.

You cannot fully eliminate “unused JavaScript” from Google’s own tags in Lighthouse; the above targets what we control on the origin.

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
| Sitemap | Terminal (repo root) | `python3 scripts/build_sitemap.py` before commit when HTML URLs change |
| Publish to GitHub | Terminal | `git add -A && git commit -m "…" && git push origin main` |
| Pull on server | cPanel → Git | **Update from Remote** |
| Go live | cPanel → Git | **Deploy HEAD Commit** |

Optional: run `scripts/package-deployment.sh` from the repo root to build a local zip (backup or manual upload); normal go-live is still Git + cPanel.
