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
- `bin/armada-launcher.py` creates a dispatch, synchronizes `FBA_READY` workers, stamps them `dispatched`, then caches dispatch-scoped foremen.
- `node-mcp-server/tools/` contains worker-facing tool handlers and storage clients.

## File Map

- `node-mcp-server/server.py`: MCP server, durable instruction cache, and Custodian sync CLI.
- `bin/armada-launcher.py`: interactive flight launcher and post-flight sync commands.
- `agents/armada-foreman.md`: version-controlled foreman agent specification for installation on the node.
- `ebay_scraper.py`: EE-647 wide-net eBay search scraper that reuses one CDP browser session across six queries and up to 60 240-item pages, deduplicating listings into incremental JSON output.
- `ebay_image_scraper.py`: EE-648 resumable eBay detail-page gallery collector that adds full-resolution gallery URL arrays to the EE-647 search JSON and emits aggregate image stats.

## Last 10 Changes

1. `AR-006`: Scoped node synchronization by required instruction status, made FBA flights select `FBA_READY` workers and transition them to `dispatched`, and updated Custodian plus the batch producer to support readiness statuses.
1. `AR-004`: Added a read-only `diagnose` launcher command plus durable foreman escalation capture and Custodian synchronization.
1. `EE-648`: Added a resumable eBay gallery URL collector that visits each search-result listing in a fresh CDP tab, regexes image hashes, and checkpoints both updated search JSON and image stats.
1. `EE-647`: Replaced the eBay detail-page POC with a paced six-query, ten-page-per-query search-lake scraper that parses current `li.s-card` results and incrementally saves deduplicated JSON.
1. `EE-646`: Added a standalone eBay motherboard scraper proof of concept that reuses the CDP pool and writes JSON and raw search/detail HTML captures for Mac-side validation.
1. `AR-003`: Added the foreman agent specification and emitted per-foreman launch prompts containing the assigned AI-ID.
1. `AR-002`: Made Custodian MCP text responses resilient to non-JSON payloads and corrected dispatch-scoped query placeholders to use the supported parameter format.
1. `AR-001`: Added dispatch-scoped instruction/dispatch synchronization, stamped worker instructions before foremen are created, and forwarded the dispatch ID to edge sync.

## Known Issues

- The local sqld endpoint at `127.0.0.1:8400` remains unavailable in this WSL checkout, so live sync and escalation delivery require Mac-node verification.
- `agents/armada-foreman.md` still permits `custodian_*`, despite AR-004 context describing node-only foremen; this pre-existing workflow mismatch was not changed by the scoped escalation work.
