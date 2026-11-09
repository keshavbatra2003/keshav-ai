#!/usr/bin/env bash
# Launch KESHAV AI natively as a desktop application (macOS & Linux)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "🚀 Launching KESHAV AI Native Desktop Window..."
python3 main.py
