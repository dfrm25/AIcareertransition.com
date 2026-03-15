# AI Career Transition Website

A comprehensive AI learning platform for professionals looking to build AI skills progressively. Built for GoDaddy cPanel hosting with easy content management.

## 🌐 Live Site
**Domain:** aicareertransition.com

## 📁 File Structure

```
AI Career Transition .com/
├── index.html          # Home page with AI readiness quiz
├── 101.html            # AI 101 Fundamentals (tools, videos, certs)
├── 201.html            # AI 201 Advanced (agents, automation, apps)
├── prompts.html        # Prompt library (200+ prompts by persona)
├── blog.html           # Blog section for tips and articles
├── apps.html           # AI apps showcase
├── feedback.html       # Feedback and contact forms
├── sitemap.xml         # SEO sitemap
├── robots.txt          # Search engine directives
├── css/
│   └── styles.css      # Main stylesheet
├── js/
│   └── main.js         # Interactive functionality
└── images/
    └── favicon.svg     # Site favicon
```

## 🚀 Deployment to GoDaddy

### Option 1: File Manager Upload
1. Log into your GoDaddy cPanel
2. Open File Manager
3. Navigate to `public_html`
4. Upload all files from this folder
5. Ensure `index.html` is at the root

### Option 2: FTP Upload
1. Use FileZilla or similar FTP client
2. Connect to your GoDaddy FTP server
3. Upload all files to `public_html`

## ✏️ Content Management Guide

### Adding Blog Posts
Edit `blog.html` and add new article cards:

```html
<article class="blog-card">
  <div class="blog-card-image" style="background: linear-gradient(...);">
    <!-- Add SVG icon or img tag -->
  </div>
  <div class="blog-card-content">
    <span class="blog-card-category">Category Name</span>
    <h3 class="blog-card-title">Your Blog Title</h3>
    <p class="blog-card-excerpt">Brief description...</p>
    <div class="blog-card-meta">
      <span>Date</span>
      <span>• X min read</span>
    </div>
  </div>
</article>
```

### Adding AI Tools
Edit `101.html` or `201.html` and add tool cards:

```html
<a href="TOOL_URL" target="_blank" rel="noopener noreferrer" class="tool-card">
  <img src="LOGO_URL" alt="Tool name logo" class="tool-card-logo">
  <div class="tool-card-name">Tool Name</div>
  <div class="tool-card-category">Category</div>
</a>
```

### Adding Prompts
Edit `prompts.html` and add prompt cards:

```html
<div class="prompt-card">
  <div class="prompt-card-header">
    <span class="prompt-card-category">Category</span>
    <button class="prompt-card-copy"><!-- Copy icon --></button>
  </div>
  <h4 class="prompt-card-title">Prompt Title</h4>
  <div class="prompt-card-text">Your prompt text here...</div>
</div>
```

### Adding New Apps
Edit `apps.html` and add app cards:

```html
<div class="app-card">
  <div class="app-card-preview">
    <!-- Add screenshot or iframe -->
  </div>
  <div class="app-card-content">
    <div class="app-card-badge">Status</div>
    <h4 class="app-card-title">App Name</h4>
    <p class="app-card-description">Description...</p>
    <div class="app-card-actions">
      <a href="APP_URL" class="btn btn-primary btn-sm">Try App</a>
    </div>
  </div>
</div>
```

### Adding Certifications
Edit `101.html` or `201.html` certification sections:

```html
<a href="CERT_URL" target="_blank" rel="noopener noreferrer" class="cert-card">
  <img src="PROVIDER_LOGO" alt="Provider logo" class="cert-card-logo">
  <div class="cert-card-content">
    <div class="cert-card-provider">Provider Name</div>
    <div class="cert-card-title">Certification Title</div>
    <div class="cert-card-meta">
      <span>🕐 Duration</span>
      <span>📜 Certificate Type</span>
    </div>
  </div>
</a>
```

### Adding Videos
Edit the appropriate HTML file and add video cards:

```html
<div class="video-card">
  <div class="video-card-thumbnail" data-video-id="YOUTUBE_VIDEO_ID">
    <img src="https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg" alt="Video title thumbnail">
    <div class="video-card-play" onclick="playVideo('VIDEO_ID', this)">
      <!-- Play icon SVG -->
    </div>
  </div>
  <div class="video-card-content">
    <div class="video-card-source">Source Name</div>
    <h4 class="video-card-title">Video Title</h4>
    <p class="video-card-description">Description...</p>
  </div>
</div>
```

## 🎨 Customization

### Color Scheme
Edit CSS variables in `css/styles.css`:

```css
:root {
  --color-accent-primary: #f59e0b;    /* Main accent (amber) */
  --color-accent-secondary: #ef4444;  /* Secondary accent (coral) */
  --color-accent-tertiary: #10b981;   /* Success color (emerald) */
  --color-accent-info: #3b82f6;       /* Info color (blue) */
}
```

### Typography
Current fonts used:
- **Display:** Outfit (headers)
- **Body:** DM Sans (paragraphs)
- **Code:** JetBrains Mono (code blocks)

## 📱 Responsive Breakpoints

- **Desktop:** > 968px
- **Tablet:** 640px - 968px
- **Mobile:** < 640px

## 🔍 SEO Checklist

- [x] Meta descriptions on all pages
- [x] Open Graph tags for social sharing
- [x] Semantic HTML structure
- [x] Sitemap.xml generated
- [x] Robots.txt configured
- [x] Mobile-responsive design
- [x] Fast loading (minimal dependencies)
- [x] Accessible (ARIA labels, skip links)

## 📊 Analytics Setup

To add Google Analytics, add this before `</head>` in all HTML files:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=YOUR_GA_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'YOUR_GA_ID');
</script>
```

## 🔄 Weekly Maintenance Tasks

1. **Content Update:** Add new tips, prompts, or blog posts
2. **Link Check:** Verify all external links still work
3. **Video Check:** Ensure embedded videos are accessible
4. **Certification Check:** Verify course links are current
5. **Analytics Review:** Check traffic and engagement metrics

## 🛠️ Technical Requirements

- **Hosting:** Any static hosting (GoDaddy cPanel, Netlify, Vercel)
- **SSL:** Required for secure connections
- **No Backend Required:** Pure HTML/CSS/JS

## 📞 Support

For technical support or questions about the website, use the feedback form at:
`/feedback.html`

---

Built with ❤️ for the AI-powered future.
