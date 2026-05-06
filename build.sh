#!/bin/bash
# Build script for Vercel deployment
# Combines landing page (docs/) and dashboard (client/) into one deployment

set -e

echo "🏗️  Building DataVint for deployment..."

# 1. Build Vue.js dashboard
echo "📦 Building Vue.js dashboard..."
cd client
npm install
npm run build
cd ..

# 2. Create deployment directory structure
echo "📁 Creating deployment structure..."
mkdir -p dist
mkdir -p dist/playground

# 3. Copy landing page to root
echo "📄 Copying landing page..."
cp -r docs/* dist/

# 4. Copy dashboard to /playground
echo "🎮 Copying dashboard to /playground..."
cp -r client/dist/* dist/playground/

echo "✅ Build complete!"
echo "📊 Deployment structure:"
echo "   / → Landing page (docs/)"
echo "   /playground → Dashboard (client/dist/)"
