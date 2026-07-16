#!/bin/bash
# ensure-cdp.sh - Ensure launchd manages the four headless Chrome CDP instances.
set -euo pipefail

PORTS=(9222 9223 9224 9225)
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"

for port in "${PORTS[@]}"; do
    label="com.armada.chrome-cdp-$port"
    plist="$LAUNCH_AGENTS/$label.plist"
    if ! launchctl list | grep "$label" >/dev/null; then
        echo "Service $label is not loaded; loading it..."
        launchctl load "$plist"
    else
        echo "Service $label: loaded"
    fi
done

sleep 2
echo
echo "=== CDP Status ==="
for port in "${PORTS[@]}"; do
    if lsof -i ":$port" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "Port $port: UP"
    else
        echo "Port $port: DOWN"
    fi
done
