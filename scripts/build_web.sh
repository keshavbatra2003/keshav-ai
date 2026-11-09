#!/usr/bin/env bash
# Script to build optimized Progressive Web App (PWA) static bundle
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "=============================================="
echo "🌐 Building KESHAV AI Progressive Web App (PWA)"
echo "=============================================="

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

flet build web \
    --project keshav_ai \
    --product "KESHAV AI" \
    --org "org.keshav.ai" \
    --base-url "/" \
    --web-renderer auto \
    -o dist/web

echo "✅ Web build complete in dist/web/! Ready for deployment on Netlify, Vercel, Firebase, or GitHub Pages."
