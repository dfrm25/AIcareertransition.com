# GoDaddy Upload Guide - AI Career Transition Website

## 📁 File Structure for GoDaddy C-Linux Hosting

Upload ALL files to the `public_html` folder in your GoDaddy cPanel.

### Required Files & Folders:

```
public_html/
├── index.html           (Homepage - REQUIRED)
├── 101.html            (AI 101 Fundamentals page)
├── 201.html            (AI 201 Advanced page)
├── prompts.html        (Prompt Library page)
├── blog.html           (Blog page)
├── apps.html           (Apps Showcase page)
├── feedback.html       (Feedback page)
├── robots.txt          (SEO - Search engine crawler instructions)
├── sitemap.xml         (SEO - Site structure for search engines)
│
├── css/
│   └── styles.css      (All website styles)
│
├── js/
│   └── main.js         (All interactive functionality)
│
└── images/
    └── favicon.svg     (Website icon)

```

## 🚀 Upload Methods

### Method 1: cPanel File Manager (Easiest)

1. **Log into GoDaddy:**
   - Go to https://sso.godaddy.com
   - Click "Manage" next to your Web Hosting (cPanel) account

2. **Open File Manager:**
   - In cPanel, find "Files" section
   - Click "File Manager"

3. **Navigate to public_html:**
   - Click on `public_html` folder (this is your website root)

4. **Upload Files:**
   - Click "Upload" button in top toolbar
   - Upload ALL files from your local folder:
     - All HTML files (index.html, 101.html, etc.)
     - robots.txt
     - sitemap.xml
   - Create folders: `css`, `js`, `images` if they don't exist
   - Upload `styles.css` to `css/` folder
   - Upload `main.js` to `js/` folder
   - Upload `favicon.svg` to `images/` folder

5. **Verify:**
   - Make sure `index.html` is directly in `public_html/`
   - Check all paths are correct

### Method 2: FTP (FileZilla)

1. **Get FTP Credentials from GoDaddy:**
   - In cPanel, go to "FTP Accounts"
   - Note your FTP hostname, username, and password

2. **Connect with FileZilla:**
   - Host: `ftp.yourdomain.com` (or IP address from GoDaddy)
   - Username: Your FTP username
   - Password: Your FTP password
   - Port: 21

3. **Upload:**
   - Navigate to `public_html` on remote (right side)
   - Navigate to your local folder (left side)
   - Drag and drop ALL files and folders to `public_html`

## ✅ Post-Upload Checklist

- [ ] `index.html` is in `public_html/` (not in a subfolder)
- [ ] All HTML files uploaded
- [ ] `css/styles.css` exists in `css/` folder
- [ ] `js/main.js` exists in `js/` folder
- [ ] `images/favicon.svg` exists in `images/` folder
- [ ] `robots.txt` and `sitemap.xml` in `public_html/`
- [ ] Test website: Visit `http://yourdomain.com` or `http://yourdomain.com/index.html`

## 🔧 Important Notes

1. **File Permissions:**
   - HTML files: 644
   - CSS/JS files: 644
   - Folders: 755

2. **If site doesn't load:**
   - Ensure `index.html` is in `public_html/` (not in a subfolder)
   - Check file permissions (should be 644 for files, 755 for folders)
   - Clear browser cache

3. **Domain Setup:**
   - If using custom domain, point it to `public_html` folder
   - DNS should point to GoDaddy nameservers (provided in your hosting account)

## 📝 Quick Test

After upload, visit:
- `http://yourdomain.com` - Should show homepage
- `http://yourdomain.com/101.html` - Should show AI 101 page
- `http://yourdomain.com/201.html` - Should show AI 201 page

---

**Need Help?** Check GoDaddy support: https://www.godaddy.com/help
