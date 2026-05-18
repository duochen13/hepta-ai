# NanoML Landing Page

This directory contains the **public-facing landing page** for https://www.datavint.io/

## 📁 Structure

```
docs/
├── index.html          # Main landing page
├── styles.css          # Landing page styles
├── particles.js        # Animated particle background
├── sitemap.xml         # SEO: Tells Google what pages exist
├── robots.txt          # SEO: Tells search engines what to crawl
├── CNAME               # Vercel custom domain configuration
└── README.md           # This file
```

## 🚀 Deployment

This directory is deployed to **Vercel** as the root (`/`) of https://www.datavint.io/

- **Landing page:** https://www.datavint.io/
- **Dashboard:** https://www.datavint.io/playground (served from `client/dist/`)

## 📝 SEO Files

### sitemap.xml
Tells Google about all pages on the site. Lists:
- Homepage: https://www.datavint.io/
- Dashboard: https://www.datavint.io/playground

### robots.txt
Tells search engines what they're allowed to crawl:
```
User-agent: *
Allow: /
Sitemap: https://www.datavint.io/sitemap.xml
```

### Meta Tags in index.html
The landing page includes comprehensive SEO meta tags:
- **Primary:** Title, description, keywords
- **Open Graph:** For Facebook/LinkedIn sharing
- **Twitter Card:** For Twitter sharing
- **Canonical URL:** Prevents duplicate content issues

## 🔍 Google Search Console

After deploying, submit the site to Google Search Console:

1. Go to: https://search.google.com/search-console
2. Add property: `https://www.datavint.io`
3. Verify ownership (Vercel auto-verifies for custom domains)
4. Submit sitemap: `https://www.datavint.io/sitemap.xml`

**Expected indexing time:** 1-7 days

## 🎨 Landing Page Features

- **Animated particle background** (particles.js)
- **Hero section** with CTAs
- **Trust bar** showing supported datasets
- **Problem-Solution-Product** sections
- **Pricing tiers**
- **Footer** with links

## 🔗 Related Directories

- **`client/`** - Vue.js dashboard (deployed to `/playground`)
- **`wiki/`** - Full documentation
- **`deployment/`** - Deployment guides and scripts
- **`examples/`** - Code examples

## 📊 Analytics (Future)

Consider adding:
- Google Analytics
- Plausible Analytics (privacy-friendly)
- Vercel Analytics (built-in)

## 🛠️ Development

To preview locally:
```bash
# Option 1: Simple HTTP server
cd docs
python -m http.server 8080
# Open http://localhost:8080

# Option 2: Live reload (requires npm install -g live-server)
cd docs
live-server
```

## 📝 Content Updates

When updating landing page content:
1. Edit `index.html` for structure
2. Edit `styles.css` for styling
3. Update `sitemap.xml` if adding new pages
4. Test locally before deploying
5. Deploy via `git push` (Vercel auto-deploys)

## ⚠️ Important Notes

- **Do NOT** add deployment scripts here (use `deployment/` directory)
- **Do NOT** add documentation here (use `wiki/` directory)
- **Keep this directory lean** - only landing page assets
- **CNAME file** is required for Vercel custom domain (do not delete)
