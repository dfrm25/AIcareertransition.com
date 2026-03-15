# Google Search Console Setup Guide

## ✅ Step-by-Step Instructions

### Step 1: Access Google Search Console

1. Go to: **https://search.google.com/search-console**
2. Sign in with your Google account (preferably the one you want to use for website management)

### Step 2: Add Your Property (Website)

1. Click **"Add Property"** button (top left)
2. Choose **"URL prefix"** (recommended - easier)
3. Enter your website URL: `https://aicareertransition.com`
4. Click **"Continue"**

### Step 3: Verify Ownership

Google needs to verify you own the website. Choose ONE of these methods:

#### Option A: HTML File Upload (Recommended - Easiest)

1. Google will provide a **HTML file** to download (e.g., `google1234567890abcdef.html`)
2. Download this file
3. Upload it to your GoDaddy `public_html` folder using File Manager
4. Click **"Verify"** in Google Search Console
5. Once verified, you can delete the file (or keep it, doesn't matter)

#### Option B: HTML Tag (Alternative)

1. Google will provide a `<meta>` tag with a verification code
2. Copy the entire `<meta>` tag
3. Open your `index.html` file in File Manager
4. Edit the file and paste the `<meta>` tag in the `<head>` section (after line 8)
5. Save the file
6. Click **"Verify"** in Google Search Console

#### Option C: Domain Name Provider (Advanced)

If you have access to your domain's DNS settings, you can add a TXT record (but HTML file is easier).

### Step 4: Submit Your Sitemap

After verification:

1. In Google Search Console, click **"Sitemaps"** in the left sidebar
2. Under **"Add a new sitemap"**, enter: `sitemap.xml`
3. Click **"Submit"**
4. Google will start crawling your site (can take a few days)

### Step 5: Request Indexing (Optional but Recommended)

1. Go to **"URL Inspection"** (top search bar)
2. Enter your homepage URL: `https://aicareertransition.com`
3. Click **"Test Live URL"**
4. If it says "URL is not on Google", click **"Request Indexing"**
5. Repeat for key pages:
   - `https://aicareertransition.com/index.html`
   - `https://aicareertransition.com/101.html`
   - `https://aicareertransition.com/201.html`
   - `https://aicareertransition.com/blog.html`

---

## 📊 What You'll See After Setup

### Performance Tab
- See which keywords are driving traffic
- Track clicks, impressions, CTR, and average position
- Monitor search trends over time

### Coverage Tab
- See which pages are indexed
- Find and fix indexing errors
- Monitor page status

### Enhancement Tabs
- Check mobile usability
- Monitor Core Web Vitals (page speed)
- See if structured data is working

---

## 🔄 Ongoing Maintenance

### Weekly Checks:
1. Check **Performance** → See which keywords are working
2. Review **Coverage** → Fix any errors
3. Monitor **Enhancements** → Ensure mobile-friendly and fast

### Monthly Tasks:
1. Review top performing pages
2. Identify new keyword opportunities
3. Check for new errors or warnings
4. Update sitemap if you add new pages

---

## 📝 Quick Checklist

- [ ] Created Google Search Console account
- [ ] Added property: `https://aicareertransition.com`
- [ ] Verified ownership (HTML file or meta tag)
- [ ] Submitted `sitemap.xml`
- [ ] Requested indexing for key pages
- [ ] Bookmarked Google Search Console for weekly checks

---

## 🎯 Key Metrics to Track

1. **Total Clicks** - How many people click from Google
2. **Total Impressions** - How many times your site appears in search
3. **Average CTR** - Click-through rate (clicks ÷ impressions)
4. **Average Position** - Your average ranking position
5. **Top Queries** - Which search terms bring traffic
6. **Top Pages** - Which pages get the most traffic

---

## 💡 Pro Tips

1. **Be Patient**: It can take 1-2 weeks for data to appear after setup
2. **Focus on Top Queries**: See what's working and create more content around those topics
3. **Fix Errors Quickly**: Google Search Console will alert you to issues - fix them ASAP
4. **Monitor Mobile**: Ensure your site is mobile-friendly (Google prioritizes mobile)
5. **Track Improvements**: Use the data to guide your content strategy

---

## 🔗 Useful Links

- Google Search Console: https://search.google.com/search-console
- Google Search Console Help: https://support.google.com/webmasters
- Sitemap Location: https://aicareertransition.com/sitemap.xml

---

**Need Help?** Google Search Console has excellent documentation and help articles. Most issues can be resolved by checking the "Coverage" and "Enhancements" tabs.
