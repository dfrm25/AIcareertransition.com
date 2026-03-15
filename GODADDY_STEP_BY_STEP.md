# GoDaddy Upload - Step-by-Step Guide

## From Your Current Dashboard View:

### Step 1: Access Hosting Management

**Option A: Via "Website" in Sidebar**
1. Click **"Website"** in the left sidebar (you can see it in your screenshot)
2. Look for **"Hosting"** or **"Manage"** button
3. Click to access your hosting account

**Option B: Via Main Dashboard**
1. Look for a section showing your hosting plan (might say "Linux Hosting" or "Web Hosting")
2. Click **"Manage"** next to it
3. This opens your hosting control panel

### Step 2: Open File Manager

Once in your hosting control panel (cPanel), you'll see many icons:

1. **Look for "Files" section** (usually in the top-left area)
2. Click on **"File Manager"** icon
   - It looks like a folder icon
   - Usually labeled "File Manager"
3. This opens a file browser

### Step 3: Navigate to public_html

1. In File Manager, you'll see a folder tree on the left
2. Click on **"public_html"** folder
   - This is your website's root directory
   - All website files go here
3. The folder will open, showing its contents

### Step 4: Upload Your Files

**Method 1: Using Upload Button (Easiest)**
1. Click **"Upload"** button at the top of File Manager
2. Click **"Select Files"** button
3. Navigate to your local folder: `AI Career Transition .com`
4. Select and upload these files ONE BY ONE or in batches:
   - `index.html`
   - `101.html`
   - `201.html`
   - `prompts.html`
   - `blog.html`
   - `apps.html`
   - `feedback.html`
   - `robots.txt`
   - `sitemap.xml`

**Method 2: Create Folders First**
1. Still in `public_html`, click **"New Folder"** button
2. Create these folders (one at a time):
   - `css`
   - `js`
   - `images`
3. Then upload files:
   - Upload `styles.css` → drag into `css` folder
   - Upload `main.js` → drag into `js` folder
   - Upload `favicon.svg` → drag into `images` folder

### Step 5: Verify Structure

After uploading, your `public_html` should look like this:

```
public_html/
├── index.html
├── 101.html
├── 201.html
├── prompts.html
├── blog.html
├── apps.html
├── feedback.html
├── robots.txt
├── sitemap.xml
├── css/
│   └── styles.css
├── js/
│   └── main.js
└── images/
    └── favicon.svg
```

## Alternative: If You Don't See File Manager

If you can't find File Manager in your dashboard:

1. Go back to your **main GoDaddy dashboard**
2. Look for **"All Products and Services"** or **"My Products"**
3. Find your **"Web Hosting"** or **"Linux Hosting"** product
4. Click **"Manage"** → This should open cPanel
5. Look for **"File Manager"** in cPanel

## Quick Tip:

If you see "Website Builder" instead of "File Manager":
- You may need to access **"cPanel"** directly
- Look for a link/button that says **"cPanel"** or **"Control Panel"**
- Once in cPanel, find "File Manager" under "Files" section

## After Upload - Test Your Site:

1. Visit: `http://aicareertransition.com`
2. Or visit: `http://aicareertransition.com/index.html`
3. If it works, you're done! ✅

---

**Need Help?** If you still can't find File Manager, take another screenshot of what you see after clicking "Website" and I can help more!
