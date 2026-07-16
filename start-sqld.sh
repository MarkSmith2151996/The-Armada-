#!/bin/bash
set -euo pipefail

ARMADA_DIR="${ARMADA_DIR:-$HOME/armada}"
CONTEXT_DB_PATH="${ARMADA_NODE_DB_PATH:-$ARMADA_DIR/node.db}"
SQLD_DB_PATH="${ARMADA_NODE_SQLD_PATH:-$ARMADA_DIR/node.sqld}"
SCHEMA_PATH="${ARMADA_NODE_SCHEMA_PATH:-$ARMADA_DIR/node-mcp-server/schema.sql}"
LISTEN_ADDR="${SQLD_HTTP_LISTEN_ADDR:-127.0.0.1:8400}"

python3 "$ARMADA_DIR/node-mcp-server/init_db.py" "$CONTEXT_DB_PATH" "$SCHEMA_PATH"

SQLD_BIN="$(command -v sqld || true)"
if [ -z "$SQLD_BIN" ] && [ -x "$HOME/.turso/sqld" ]; then
  SQLD_BIN="$HOME/.turso/sqld"
fi

if [ -z "$SQLD_BIN" ]; then
  printf 'sqld is not installed. Install it with: curl -sSfL https://get.tur.so/install.sh | bash\n' >&2
  exit 127
fi

exec "$SQLD_BIN" --db-path "$SQLD_DB_PATH" --http-listen-addr "$LISTEN_ADDR"
