#!/usr/bin/env bash
# Package KESHAV AI as a standalone macOS Desktop Application (.app / .dmg)
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "=============================================="
echo "🍏 Building KESHAV AI for macOS Desktop"
echo "=============================================="

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

flet build macos \
    --project keshav_ai \
    --product "KESHAV AI" \
    --org "org.keshav.ai" \
    --bundle-id "org.keshav.ai.desktop" \
    --build-version "1.0.0" \
    --build-number 1 \
    -o dist/macos

echo "✅ macOS Desktop App built in dist/macos/!"
