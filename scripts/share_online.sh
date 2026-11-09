#!/usr/bin/env bash
# Start or get the live public shareable link for KESHAV AI using Cloudflare Tunnel
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

mkdir -p "$DIR/bin" "$DIR/logs"

CLOUDFLARED="$DIR/bin/cloudflared"

# Download cloudflared if not present
if [ ! -f "$CLOUDFLARED" ]; then
    echo "📥 Downloading Cloudflare Tunnel utility..."
    curl -L -s -o "$DIR/bin/cloudflared.tgz" "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
    tar -xzf "$DIR/bin/cloudflared.tgz" -C "$DIR/bin"
    rm -f "$DIR/bin/cloudflared.tgz"
    chmod +x "$CLOUDFLARED"
fi

# Check if tunnel is already active
TUNNEL_PID=$(pgrep -f "cloudflared tunnel --url" || true)

if [ -z "$TUNNEL_PID" ]; then
    echo "🌐 Starting secure public Cloudflare Tunnel..."
    nohup "$CLOUDFLARED" tunnel --url http://localhost:8550 > "$DIR/logs/tunnel.log" 2>&1 &
    sleep 4
fi

# Extract public URL
SHARE_URL=$(grep -o 'https://[-a-zA-Z0-9@:%._+~#=]*.trycloudflare.com' "$DIR/logs/tunnel.log" | tail -n 1 || true)
LAN_IP=$(ipconfig getifaddr en0 || echo "127.0.0.1")

if [ -n "$SHARE_URL" ]; then
    # Update SQLite database so UI has the live link
    if [ -d ".venv" ]; then
        .venv/bin/python3 -c "import database; database.set_setting('share_url', '$SHARE_URL'); database.set_setting('lan_url', 'http://$LAN_IP:8550')" || true
    fi

    echo "========================================================="
    echo "🎉 KESHAV AI PUBLIC SHAREABLE LINK IS READY!"
    echo "========================================================="
    echo "🌍 Public Worldwide HTTPS Link (WhatsApp / Clipboard):"
    echo "   $SHARE_URL"
    echo ""
    echo "🏠 Home Wi-Fi LAN Link:"
    echo "   http://$LAN_IP:8550"
    echo "========================================================="
else
    echo "Tunnel started. Check $DIR/logs/tunnel.log for connection details."
fi
