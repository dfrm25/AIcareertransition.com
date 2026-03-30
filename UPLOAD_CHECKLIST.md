# Upload checklist (legacy FTP)

**Primary process:** Git deploy — see **[DEPLOYMENT.md](DEPLOYMENT.md)** (Cursor → GitHub → cPanel **Deploy HEAD Commit**).

This checklist was for manual File Manager uploads. Use **[DEPLOY_MANIFEST.txt](DEPLOY_MANIFEST.txt)** if you still need a file-by-file verification list for `public_html`.

---

## Legacy steps (FTP only)

- [ ] Compared `public_html` to `DEPLOY_MANIFEST.txt`
- [ ] `ads.txt` present at site root (AdSense)
- [ ] `robots.txt`, `sitemap.xml` present
- [ ] `css/styles.css`, `js/main.js`, `images/` including `blog/` assets
- [ ] All HTML pages including `career.html` and `blog/*.html`
