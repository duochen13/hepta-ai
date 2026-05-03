#!/bin/bash

echo "🚀 HeptaAI Website Deployment"
echo "=============================="
echo ""
echo "Choose deployment method:"
echo ""
echo "1) Surge.sh (Fastest - 30 seconds)"
echo "   → https://heptaai.surge.sh"
echo ""
echo "2) GitHub Pages (Free forever)"
echo "   → https://duochen13.github.io/hepta-ai"
echo ""
echo "3) Netlify (Professional)"
echo "   → https://heptaai.netlify.app"
echo ""
read -p "Enter choice (1, 2, or 3): " choice

case $choice in
    1)
        echo ""
        echo "📦 Deploying to Surge.sh..."
        echo ""
        echo "First time? You'll need to create an account (takes 10 seconds)"
        echo ""
        cd "$(dirname "$0")"
        surge . heptaai.surge.sh
        ;;
    2)
        echo ""
        echo "📝 To deploy via GitHub Pages:"
        echo ""
        echo "1. Visit: https://github.com/duochen13/hepta-ai/settings/pages"
        echo "2. Under 'Source': Select 'main' branch"
        echo "3. Under 'Folder': Select '/website'"
        echo "4. Click 'Save'"
        echo ""
        echo "Your site will be live at:"
        echo "https://duochen13.github.io/hepta-ai"
        echo ""
        echo "Opening GitHub Pages settings..."
        open "https://github.com/duochen13/hepta-ai/settings/pages"
        ;;
    3)
        echo ""
        echo "📦 Deploying to Netlify..."
        echo ""
        if command -v netlify &> /dev/null; then
            cd "$(dirname "$0")"
            netlify deploy --prod
        else
            echo "Installing Netlify CLI..."
            npm install -g netlify-cli
            cd "$(dirname "$0")"
            netlify deploy --prod
        fi
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Deployment complete!"
