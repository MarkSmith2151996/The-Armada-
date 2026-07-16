#!/bin/bash
set -euo pipefail

ARMADA_DIR="${ARMADA_DIR:-$HOME/armada}"

echo "Starting Armada node services..."

echo "Starting Chrome CDP..."
"$ARMADA_DIR/start-chrome-cdp.sh"

echo "Starting sqld..."
"$ARMADA_DIR/start-sqld.sh" > /dev/null 2>&1 &

echo "Starting SearXNG..."
"$ARMADA_DIR/start-searxng.sh" start

echo "Node MCP Server is stdio-based and starts when an MCP client connects."
echo "All services started."
echo "  Chrome CDP: localhost:9222"
echo "  sqld: localhost:8400"
echo "  SearXNG: localhost:8888"
echo "  Node MCP: starts on client connect"
