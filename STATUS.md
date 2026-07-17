# The Armada

## User-Owned Notes

- Edge-node and launcher repository for dispatching Armada outreach flights.

<!-- AUTO-MANAGED -->

## Key Config

- Node MCP server: `node-mcp-server/server.py`
- Launcher: `bin/armada-launcher.py`
- Local sqld endpoint: `SQLD_URL` (defaults to `http://127.0.0.1:8400`)
- Custodian endpoint: `CUSTODIAN_MCP_URL`
- Task prefix: `AR`

## Architecture

- `node-mcp-server/server.py` exposes worker tools and synchronizes instruction/dispatch state with Custodian.
- `bin/armada-launcher.py` creates a dispatch, assigns workers to foremen, and invokes node synchronization.
- `node-mcp-server/tools/` contains worker-facing tool handlers and storage clients.

## File Map

- `node-mcp-server/server.py`: MCP server, durable instruction cache, and Custodian sync CLI.
- `bin/armada-launcher.py`: interactive flight launcher and post-flight sync commands.

## Last 10 Changes

1. `AR-002`: Made Custodian MCP text responses resilient to non-JSON payloads and corrected dispatch-scoped query placeholders to use the supported parameter format.
1. `AR-001`: Added dispatch-scoped instruction/dispatch synchronization, stamped worker instructions before foremen are created, and forwarded the dispatch ID to edge sync.

## Known Issues

- The local sqld endpoint at `127.0.0.1:8400` was unavailable during AR-001 verification, so live sync CLI calls could not reach Custodian.
