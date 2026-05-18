# NanoML Landing Page

A modern, Apple-inspired landing page for NanoML - The Next Generation Training Data Compiler.

## Design Features

- **Apple-like Aesthetic**: Deep black background (#000000) with vivid purple accents (#6366F1)
- **Animated Particle Network**: Interactive dot mesh background with connecting lines (OceanBase-inspired)
- **Mouse Interaction**: Particles react to cursor movement with smooth physics
- **Glowing Effects**: Shadows and glows on interactive elements and logos
- **Premium Typography**: Inter font with clear hierarchy (64px headlines, 56px sections)
- **Responsive Design**: Mobile-first approach with breakpoints for tablet and desktop
- **High Contrast**: White text on black backgrounds for maximum readability
- **Visual Depth**: Layered shadows and glassmorphism effects

## File Structure

```
docs/                   # Website files (GitHub Pages serves from /docs)
├── index.html          # Main HTML structure (landing page)
├── styles.css          # Complete styling with Apple-like aesthetics
├── particles.js        # Animated dot mesh network background
├── deploy.sh           # Deployment script with 3 hosting options
└── deploy.md           # Deployment instructions

wiki/                   # Documentation
├── api/                # API documentation
├── features/           # Feature documentation
├── changelog/          # Design specs
└── website/            # Website documentation
    ├── README.md       # Website customization guide (this file)
    └── website-structure-analysis.md  # Competitor analysis
```

## Sections

1. **Announcement Bar** - Social proof with Kaggle results
2. **Hero Section** - "Training Data Compiler" pitch with dual CTAs
3. **Trust Bar** - Dataset logos (Kaggle, UCI ML, OpenML, MovieLens, Amazon)
4. **Problem Section** - Three pain point cards (light background)
5. **System Differentiator** - Traditional Tools vs NanoML comparison (black background)
6. **Integration Section** - Data frameworks (Pandas, Spark, Dask, Polars) + ML frameworks (Scikit-learn, PyTorch, TensorFlow, XGBoost) with glowing logos
7. **Testimonials** - Three customer quotes (black background)
8. **Validation Pipeline** - 4-step workflow (Detect → Fix → Measure → Ship)
9. **Results Section** - Real Titanic metrics with large numbers
10. **Final CTA** - Purple gradient section with conversion buttons
11. **Footer** - Links organized by category

## How to Use

### Local Development

1. Open `index.html` in your browser:
   ```bash
   cd docs
   open index.html
   # or
   python -m http.server 8000
   # then visit http://localhost:8000
   ```

2. Edit content in `docs/index.html`
3. Edit styles in `docs/styles.css`
4. Edit particle effects in `docs/particles.js`

### Deploy to Production

#### Option 1: Netlify (Easiest)
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
cd website
netlify deploy --prod
```

#### Option 2: Vercel
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd website
vercel --prod
```

#### Option 3: GitHub Pages (Recommended)
1. Go to https://github.com/duochen13/datavint/settings/pages
2. Under "Source" → Select "Deploy from a branch"
3. Under "Branch" → Select "main"
4. Under "Folder" → Select "/docs"
5. Click "Save"
6. Your site will be live at `https://duochen13.github.io/datavint/`

#### Option 4: AWS S3 + CloudFront
```bash
# Upload to S3 bucket
aws s3 sync . s3://your-bucket-name --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

## Customization

### Colors
Update these CSS variables in `styles.css`:

```css
/* Primary brand color */
#6366F1 → Your brand purple

/* Background */
#000000 → Your dark background

/* Text colors */
#FFFFFF → Primary text
#A1A1AA → Secondary text
#71717A → Tertiary text
```

### Fonts
The site uses **Inter** from Google Fonts. To change:

1. Update the font import in `index.html`:
```html
<link href="https://fonts.googleapis.com/css2?family=YourFont:wght@400;600;700&display=swap" rel="stylesheet">
```

2. Update `font-family` in `styles.css`:
```css
font-family: 'YourFont', sans-serif;
```

### Content
Edit text directly in `index.html`. Key sections:
- Hero headline and subline
- Testimonials (replace with real customer quotes)
- Integration logos (now using real framework logos)
- Metrics (update with your real data)

### Particle Network Animation
Customize the background animation in `particles.js`:

```javascript
this.numberOfParticles = 80;     // Number of dots (default: 80)
this.maxDistance = 150;          // Max distance for connecting lines (default: 150)
this.mouse.radius = 150;         // Mouse interaction radius (default: 150)
```

Colors (in `particles.js`):
```javascript
// Particle color
fillStyle = 'rgba(99, 102, 241, 0.5)';  // Purple dots

// Connection lines color
strokeStyle = `rgba(99, 102, 241, ${opacity * 0.3})`;  // Purple lines
```

To disable the animation, simply remove:
```html
<canvas id="particle-canvas"></canvas>
<script src="particles.js"></script>
```

## Performance Optimization

### Before Production:

1. **Minify CSS**:
   ```bash
   npx csso styles.css -o styles.min.css
   ```

2. **Optimize Images** (if you add any):
   - Use WebP format
   - Compress with tools like ImageOptim or TinyPNG

3. **Add Analytics**:
   ```html
   <!-- Google Analytics -->
   <script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
   ```

4. **Add Meta Tags** for SEO:
   ```html
   <meta name="description" content="NanoML - The next generation training data compiler">
   <meta property="og:title" content="NanoML">
   <meta property="og:description" content="Optimize your dataset without changing your model">
   <meta property="og:image" content="https://yoursite.com/og-image.png">
   ```

## Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile browsers: ✅ Responsive design

## Next Steps

1. **Replace placeholder logos** with actual SVG/PNG brand assets
2. **Add real testimonials** from beta users
3. **Implement CTAs** - connect buttons to signup/demo booking forms
4. **Add analytics** - Google Analytics or Plausible
5. **SEO optimization** - meta tags, sitemap, robots.txt
6. **Performance testing** - Lighthouse, PageSpeed Insights

## Tech Stack

- Pure HTML5
- Pure CSS3 (no frameworks)
- Vanilla JavaScript (Canvas API for particle animation)
- Google Fonts (Inter)

## License

This landing page design is part of the NanoML project.
