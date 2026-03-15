# Fix Redirect to /lander Issue

## Problem:
Website is redirecting to `/lander` instead of showing `index.html`

## Solution:

### Option 1: Delete/Rename the lander page (Easiest)

1. In File Manager, look for any file or folder named `lander`
2. Delete it or rename it to `lander.old`
3. This will allow `index.html` to load

### Option 2: Create .htaccess file (Recommended)

Create a `.htaccess` file in `public_html` to force `index.html` as the default:

1. In File Manager, click "+ File" button
2. Name it: `.htaccess` (note the dot at the beginning)
3. Add this content:

```
DirectoryIndex index.html index.htm index.php
```

4. Save the file

### Option 3: Check GoDaddy Settings

1. Go back to GoDaddy hosting dashboard
2. Look for "Domain Settings" or "Website Settings"
3. Check if there's a default page set to "lander"
4. Change it to "index.html"

---

## Quick Fix Steps:

1. **Check File Manager for `lander` file/folder:**
   - Look in `public_html` folder
   - If you see `lander` or `lander.html` or `lander/` folder, delete or rename it

2. **Create `.htaccess` file:**
   - Click "+ File" in File Manager
   - Name: `.htaccess`
   - Content: `DirectoryIndex index.html index.htm index.php`
   - Save

3. **Test:**
   - Visit: `http://aicareertransition.com`
   - Should now show your index.html page
