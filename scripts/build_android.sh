#!/usr/bin/env bash
# Script to build standalone Android APK or Google Play App Bundle (AAB)
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "=============================================="
echo "🚀 Building KESHAV AI for Android"
echo "=============================================="

# Ensure virtual environment is activated
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

BUILD_TYPE="${1:-apk}"

if [ "$BUILD_TYPE" == "aab" ]; then
    echo "📦 Packaging Android App Bundle (AAB) for Google Play Store..."
    flet build aab \
        --project keshav_ai \
        --product "KESHAV AI" \
        --org "org.keshav.ai" \
        --build-version "1.0.0" \
        --build-number 1 \
        -o dist/android
    echo "✅ Android App Bundle created in dist/android/"
else
    echo "📦 Packaging Android APK for direct installation..."
    flet build apk \
        --project keshav_ai \
        --product "KESHAV AI" \
        --org "org.keshav.ai" \
        --build-version "1.0.0" \
        --build-number 1 \
        -o dist/android
    echo "✅ Android APK created in dist/android/"
fi
