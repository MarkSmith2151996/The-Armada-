# Armada Node MCP Server

Standalone MCP server for Armada worker nodes. It exposes only the worker-facing tools needed for wholesale outreach research:

- `search_brand`
- `browse_page`
- `get_context`
- `record_verdict`

Bulky tool results are written to the local node context DB at `~/armada/node.db`. Workers receive compact responses and can retrieve earlier results through `get_context` instead of carrying old results in every turn.

## Run

```bash
python3 -m venv ~/armada/node-mcp-server/.venv
~/armada/node-mcp-server/.venv/bin/python -m pip install -r ~/armada/node-mcp-server/requirements.txt
~/armada/start-chrome-cdp.sh
~/armada/start-sqld.sh
~/armada/node-mcp-server/.venv/bin/python ~/armada/node-mcp-server/server.py
```

The server runs over MCP stdio by default.

## Environment

```bash
export ARMADA_NODE_DB_PATH=~/armada/node.db
export ARMADA_NODE_SQLD_PATH=~/armada/node.sqld
export ARMADA_NODE_NAME=macbook
export SEARXNG_SEARCH_URL=http://127.0.0.1:8888/search
export ARMADA_CDP_ENDPOINT=http://127.0.0.1:9222
export FBA_POSTGRES_DSN='postgresql://user:pass@host:5432/hive?options=-csearch_path%3Dfba'
export CUSTODIAN_MCP_URL=https://custodian.lamannalogistics.com/mcp
```

`record_verdict` degrades safely if `FBA_POSTGRES_DSN` is unset or `psycopg2` is not installed. It returns explicit warnings instead of silently dropping work.

The installed `sqld` 0.24.x binary uses a storage directory, so `~/armada/start-sqld.sh` exposes sqld from `ARMADA_NODE_SQLD_PATH` while the MCP server keeps its SQLite-compatible context DB at `ARMADA_NODE_DB_PATH`.
