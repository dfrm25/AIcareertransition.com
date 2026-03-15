# Blog Upload Checklist

## ✅ Local File Status
- File: `blog.html` (16KB)
- Contains: "5 Prompting Best Practices That Actually Work"
- Date: January 20, 2025
- Status: ✅ READY TO UPLOAD

## 🔍 Troubleshooting Steps

### 1. Verify File Location on GoDaddy
- Go to: **cPanel → File Manager**
- Navigate to: `public_html/`
- Check if `blog.html` exists there
- **File size should be ~16KB** (not smaller)

### 2. Upload Process
1. In File Manager, go to `public_html/`
2. **Delete the old `blog.html`** (if it exists)
3. **Upload the new `blog.html`** from your local computer
4. Make sure it's in `public_html/` (not in a subfolder)

### 3. Clear Cache
- **Browser cache**: Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
- **GoDaddy cache**: If you have caching enabled, clear it
- **CDN cache**: If using Cloudflare or similar, purge cache

### 4. Verify Upload
After uploading, check:
- File size matches (should be ~16KB)
- File modification date is recent
- File is in `public_html/` (root directory)

### 5. Test URL
Visit: `https://aicareertransition.com/blog.html`
- Should show "5 Prompting Best Practices That Actually Work"
- Should NOT show "No posts yet — coming soon."

## ⚠️ Common Issues

**Issue**: Still seeing old content
- **Solution**: Clear browser cache, try incognito/private window

**Issue**: File uploaded but wrong content
- **Solution**: Make sure you uploaded the correct file from your local folder

**Issue**: 404 error
- **Solution**: Check file is in `public_html/` not a subfolder

**Issue**: File size is different
- **Solution**: Re-upload the file - it may have been corrupted

## 📁 File Details
- **Local file path**: `/Users/richamathur/Desktop/AI experiments/Cursor Projects /AI Career Transition .com/blog.html`
- **Server path**: `public_html/blog.html`
- **File size**: ~16KB
- **Contains**: Featured post + blog post about prompting best practices