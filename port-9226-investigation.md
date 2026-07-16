# Port 9226 Investigation

Date: 2026-07-14 UTC

## Finding

Port 9226 was created by `~/armada/preflight.sh`, not by `ensure-cdp.sh`.

The listener was Chrome PID 24046, launched on 2026-07-13 at 15:15:05 with:

```text
/Applications/Google Chrome.app/Contents/MacOS/Google Chrome \
  --remote-debugging-port=9226 \
  --user-data-dir=/Users/tubslamanna/chrome-cdp-9226 \
  --no-first-run \
  --disable-default-apps
```

It was headed (no `--headless` flag) and orphaned under `launchd` (PPID 1). It listened only on `127.0.0.1:9226`.

## Evidence

- `preflight.sh` defines `NEEDED_PORTS=(9222 9223 9224 9225 9226)` at line 28.
- When a listed port is missing, `preflight.sh` calls `open -na "Google Chrome" --args` with `--remote-debugging-port=$port` and `--user-data-dir=$HOME/chrome-cdp-$port` at lines 34-40.
- Those flags and profile path exactly match PID 24046. The script does not use `--headless`, explaining the headed process.
- `ensure-cdp.sh` only manages ports 9222 through 9225 and launches them headless with `/tmp/chrome-$port`; it did not create 9226.
- The current Node MCP `CDPPool` uses base port 9222 with `MAX_INSTANCES = 9`, so its configured range is 9222 through 9230. It discovers existing ready endpoints during initialization and can adopt an external listener such as 9226.
- Historical OpenCode session records show several workers received `9226` from `armada-node_acquire_cdp`, including AI-84015, AI-84154, AI-84208, and AI-84290. Thus 9226 was repeatedly offered by the pool rather than being a one-off browse parameter.

## Why Browsing Failed

`tools/browse_page.py` connects through CDP and uses the existing browser context when available. If none is available, it attempts `browser.new_context()`.

The headed preflight Chrome on 9226 produced `Browser.setDownloadBehavior: Browser context management is not supported` during the Playwright CDP path. This incompatible external Chrome was then selected by the pool, causing 14 recorded browse failures and premature INCONCLUSIVE outcomes.

The exact underlying Chrome limitation is not separately identified by the process list, but the failure is tied to the preflight-launched headed/profiled instance and not to the managed headless launch configuration.

## Remediation Performed

- Killed only the listener on port 9226: PID 24046.
- Verified that PID 24046 no longer exists and `lsof -nP -iTCP:9226 -sTCP:LISTEN` returns no listener.
- No other service was restarted or modified.

## Recommendation

1. Remove 9226 from the preflight script's required-port list or make preflight invoke the same headless launcher and profile convention as the managed pool.
2. Keep one port authority: the pool should own its entire configured range, rather than adopting arbitrary ready endpoints in it.
3. Restrict the pool to the intended four ports (9222-9225) unless a larger pool is deliberately configured and launched headless.
4. Add a preflight validation that rejects a listener without `--headless` or the expected profile before a worker can use it.
5. Preserve the worker rule that the returned CDP port, not a hard-coded 9222, is the browser target.
