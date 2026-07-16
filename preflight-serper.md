# Wave 2 Serper Pre-Flight

Generated: 2026-07-14

## Status

Foreman and dispatch records are prepared in Custodian, but this flight is **not launch-ready** until the Mac can synchronize its local sqld cache with Custodian. No foremen or workers were launched.

The original five-foreman plan was changed by user direction to four foremen because the approved node MCP configuration has a four-port CDP pool (`9222`-`9225`).

## Flight 2 Reconciliation

- Real missing-verdict brands checked: 7.
- Recovered verdicts: 0.
- Requeued for Serper-powered re-execution: 7.
- Skipped non-brand test session: 1 (`test`).
- No missing session had a recorded `record_verdict` final result in `node.db`.
- Reopened instructions: `AI-86172` (Wright Products), `AI-85442` (Plink), `AI-85443` (Port Authority), `AI-85447` (SureFire), `AI-85451` (ZOUT), and `AI-85454` (ALPHA LION).
- Jack's Classic (`AI-86282`) was already open.
- Custodian open brand-outreach worker count after reconciliation: 426.

## Health Check

| Check | Result | Notes |
| --- | --- | --- |
| Custodian from Mac | BLOCKED | `http://100.95.20.98:8223/mcp` timed out; configured `https://custodian.lamannalogistics.com/mcp` also timed out. |
| sqld | PASS | `http://127.0.0.1:8400/health` returned HTTP 200. |
| Chrome CDP | PASS | Ports `9222`, `9223`, `9224`, and `9225` are listening. |
| Serper API | PASS | Returned official Duck Brand and Shurtape results for the test query. |
| Node MCP import | PASS | `import server` completed without error. |
| CDP acquire/release | PASS | Acquired and released port `9222`. |
| `search_brand` backend | PASS | Returned `Serper: 9 search results` and `https://www.duckbrand.com/contact` as the first result. |
| Pre-flight sync | BLOCKED | `python server.py --sync-from-custodian` timed out to the configured Custodian endpoint. |
| Local/Custodian worker count | BLOCKED | Custodian has 426 open workers; local sqld remains stale at 420 open workers because sync cannot complete. |

## Foremen And Dispatches

| Foreman | Dispatch | CDP port | Workers | Ordered range | Status |
| --- | --- | --- | ---: | --- | --- |
| `AI-86525` | `D-W2-SERPER-F1` | 9222 | 107 | `AI-83473:AI-85459` | open / pending |
| `AI-86526` | `D-W2-SERPER-F2` | 9223 | 107 | `AI-85460:AI-85874` | open / pending |
| `AI-86527` | `D-W2-SERPER-F3` | 9224 | 106 | `AI-85875:AI-86235` | open / pending |
| `AI-86528` | `D-W2-SERPER-F4` | 9225 | 106 | `AI-86242:AI-86465` | open / pending |

All foremen use `deepseek/deepseek-v4-flash`, contain their explicit ordered worker ID lists, and state that `SERPER_API_KEY` must be supplied in the launch environment without embedding it in the instructions.

## Required Before Launch

Restore Mac connectivity to the configured Custodian MCP endpoint, then run:

```bash
export SERPER_API_KEY='[configured secret]'
python3 server.py --sync-from-custodian
```

Confirm local sqld shows 426 open workers and the four new open foremen before launching any foreman.
