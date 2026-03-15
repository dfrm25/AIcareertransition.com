# Troubleshooting - Website Not Showing

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
