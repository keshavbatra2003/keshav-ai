#!/usr/bin/env bash
# Script to build iOS IPA or iOS Simulator App
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "=============================================="
echo "🍏 Building KESHAV AI for iOS"
echo "=============================================="

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

TARGET="${1:-simulator}"

if [ "$TARGET" == "ipa" ]; then
    echo "📦 Packaging iOS IPA for TestFlight / App Store..."
    flet build ipa \
        --project keshav_ai \
        --product "KESHAV AI" \
        --org "org.keshav.ai" \
        --bundle-id "org.keshav.ai.assistant" \
        --build-version "1.0.0" \
        --build-number 1 \
        -o dist/ios
    echo "✅ iOS IPA package built in dist/ios/"
else
    echo "📱 Building iOS Simulator .app bundle..."
    flet build ios-simulator \
        --project keshav_ai \
        --product "KESHAV AI" \
        --org "org.keshav.ai" \
        --bundle-id "org.keshav.ai.assistant" \
        --build-version "1.0.0" \
        --build-number 1 \
        -o dist/ios-simulator
    echo "✅ iOS Simulator app built in dist/ios-simulator/"
fi
