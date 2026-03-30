# Troubleshooting - Website Not Showing

---

## Issue: cPanel Git — "The system could not retrieve the remote branches"

This means the **server cannot talk to GitHub** (network, DNS, TLS) or **GitHub is rejecting the connection** (private repo without credentials, or auth no longer allowed).

### 1. Confirm the repo is reachable from the server (best first test)

In **cPanel → Terminal** (or SSH into the account), run:

```bash
curl -sI https://github.com | head -n 3
cd ~/repositories/AIcareertransition.com
git remote -v
git ls-remote https://github.com/dfrm25/AIcareertransition.com.git HEAD
```

- If **`curl` fails** or **`git ls-remote` hangs/errors** → hosting **outbound access** or **DNS** problem. Open a ticket with GoDaddy: *“Outbound HTTPS to github.com from cPanel fails.”*
- If **`git ls-remote` asks for a username/password** or returns **401/403** → **authentication** (see below).

### 2. If the GitHub repo is **private**

cPanel’s “pull from GitHub” over **HTTPS** does not use your Mac login; the server needs access.

**Option A — make the repo public** (simplest for a static site), then use **Try Again** / **Update** in Git Version Control.

**Option B — keep it private:** in GitHub → **Settings → Deploy keys** → add an **SSH deploy key** (generate key pair on the server in Terminal, add **public** key to GitHub). Then in cPanel, switch the clone to use the **SSH** remote URL if your Git UI supports it, or manage pulls via Terminal with that remote.

**Option C — Personal Access Token (HTTPS):** GitHub no longer accepts account passwords for Git. Create a **fine-grained or classic PAT** with repo read, then configure the server remote to use  
`https://<TOKEN>@github.com/dfrm25/AIcareertransition.com.git`  
(only if you are comfortable storing a token on the server; rotate if exposed).

### 3. If the repo is **public** but cPanel still errors

- Click **Update** next to the warning, then **Try Again**.
- In **Git Version Control**, confirm **Remote URL** is exactly:  
  `https://github.com/dfrm25/AIcareertransition.com.git`
- **Remove and re-create** the repository in cPanel (clone again). **Back up** `public_html` if you have uncommitted live edits first.

### 4. After remote works again

Use **Pull or Deploy → Update from Remote**, then **Deploy HEAD Commit** as in `DEPLOYMENT.md`.

---

## Issue: Files uploaded but website not showing

### Step 1: Verify Folder Contents

You need to check if files are INSIDE the folders:

1. **Double-click the `css` folder** in File Manager
   - You should see `styles.css` inside
   - If it's empty, upload `styles.css` into this folder

2. **Double-click the `js` folder** in File Manager
   - You should see `main.js` inside
   - If it's empty, upload `main.js` into this folder

3. **Double-click the `images` folder** in File Manager
   - You should see `favicon.svg` inside
   - If it's empty, upload `favicon.svg` into this folder

### Step 2: Check Domain Setup

Your domain might not be pointing to this hosting:

1. Go back to GoDaddy dashboard
2. Check if `aicareertransition.com` is connected to this hosting account
3. Domain should point to: `public_html` directory

### Step 3: Clear Cache & Test

1. Clear browser cache (Ctrl+Shift+Delete or Cmd+Shift+Delete)
2. Try accessing: `http://aicareertransition.com/index.html`
3. Or try: `http://your-server-ip/index.html` (if domain isn't set up yet)

### Step 4: Check File Permissions

All files should have permissions:
- Files: 644
- Folders: 755

This is usually set automatically, but check if needed.

### Step 5: Verify index.html Location

Make sure `index.html` is directly in `public_html/` (not in a subfolder)

---

## Most Common Issue:

**Files are in the WRONG location!**

Make sure:
- `styles.css` is INSIDE `css/` folder (not next to it)
- `main.js` is INSIDE `js/` folder (not next to it)
- `favicon.svg` is INSIDE `images/` folder (not next to it)
