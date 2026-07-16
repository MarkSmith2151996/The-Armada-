# browse_page Fix Report

## Root cause

`browse_page` was failing for two reasons at the same time:

1. The browser-use LLM backend at `http://100.95.20.98:4096/v1` is unstable and resets requests. Raw `curl` calls to `/v1/models` and `/v1/chat/completions` reset the connection, and browser-use logs show repeated `ModelProviderError: Connection error.` failures.
2. Multiple overlapping browser-use runs were colliding with each other. The service logs showed concurrent Chrome/CDP sessions tearing down while sibling requests were still running, producing `WebSocket connection closed`, `Failed to establish CDP connection`, and reconnection spam.

There was also a masking bug: browser-use could complete without a real final answer, and the service would still hand back a truthy-looking payload instead of a failure.

## Fix applied

### 1. Bounded concurrency in browser-use service

File: `/Users/tubslamanna/browser-use-service/server.py`

- Added `BROWSER_USE_MAX_CONCURRENT` with a default of `2`
- Added an async semaphore so only 2 browser-use requests run at once
- Added per-request queue/acquire/finish logging

### 2. Reject empty browser-use completions

File: `/Users/tubslamanna/browser-use-service/server.py`

- Treat `final_result() == None` as a failure
- Return `success: false` with `error: browser-use completed without a final result`

### 3. Direct-fetch fallback in node MCP `browse_page`

File: `/Users/tubslamanna/armada/node-mcp-server/tools/browse_page.py`

- If browser-use times out, crashes, or returns no usable result, fall back to a direct HTTP fetch
- Extract readable text from HTML without using the browser-use LLM path
- Store fallback metadata, including the original browser-use error
- Detect and reject browser-use agent-history dumps that only contain failure noise

### 4. Service restart correction

- Restarted `browser-use-service` with its venv interpreter:
  `/Users/tubslamanna/browser-use-service/venv/bin/python server.py`

## Verification

### Health

- `curl http://127.0.0.1:8096/health` returned `{"status":"ok",...}`

### 3 simultaneous browse_page calls

Ran 3 concurrent `handle_browse_page(...)` calls against:

- `https://example.com`
- `https://example.org`
- `https://httpbin.org/html`

Result:

- All 3 returned `ok: true`
- Fallback engaged where browser-use timed out or returned no result
- Text content was returned for all 3 calls

### Concurrency queue evidence

`server.log` now shows queued requests waiting for an available slot, for example:

- `browse request be105f67 acquired slot`
- `browse request d793daca acquired slot`
- `browse request 6fa1e271 waiting for slot (2 max)`
- `browse request 6fa1e271 acquired slot`

This confirms the service is now gating concurrent browser runs.

### Zombie Chrome check

- `ps aux | grep -E "[Cc]hrome.*--headless|chromium" | grep -v grep` returned no matches after verification

## Remaining risk

The upstream LLM proxy at `100.95.20.98:4096` is still unhealthy. The new fixes stop `browse_page` from hard-failing and prevent concurrent browser-use overload, but full browser-use automation quality will remain degraded until that proxy is repaired.
