#!/bin/bash
set -euo pipefail

ARMADA_DIR="${ARMADA_DIR:-$HOME/armada}"
LOG_DIR="${ARMADA_LOG_DIR:-$ARMADA_DIR/logs}"
LOG_FILE="$LOG_DIR/chrome-cdp.log"
CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

mkdir -p "$LOG_DIR"

for port in 9222 9223 9224 9225; do
  if curl -s "http://localhost:$port/json/version" > /dev/null 2>&1; then
    echo "Chrome CDP already running on port $port"
    continue
  fi

  user_data_dir="$HOME/chrome-cdp-$port"
  mkdir -p "$user_data_dir"

  nohup "$CHROME_BIN" \
    --headless=new \
    --remote-debugging-port="$port" \
    --user-data-dir="$user_data_dir" \
    --remote-allow-origins=* \
    --disable-gpu \
    --no-sandbox \
    >> "$LOG_FILE" 2>&1 &

  echo "Chrome CDP started on port $port"
  sleep 1
done
