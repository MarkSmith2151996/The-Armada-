#!/usr/bin/env python3
"""Dump open brand-outreach worker instructions into the Node MCP cache."""

import json
import urllib.error
import urllib.request
from pathlib import Path


CUSTODIAN_URL = "http://100.95.20.98:8223/mcp"
TOKEN = "96b2acbc0ae6cb1597ce4c3998938d28b7e5f8805b51deb795afa815aa6b75df"
OUTPUT = Path("/Users/tubslamanna/armada/node-mcp-server/instructions.json")
SESSION_ID = ""


def parse_response(raw: bytes) -> dict:
    """Accept normal JSON or the final JSON payload in an SSE response."""
    text = raw.decode("utf-8")
    if text.lstrip().startswith("{"):
        return json.loads(text)

    events = []
    for line in text.splitlines():
        if line.startswith("data:"):
            events.append(json.loads(line.removeprefix("data:").strip()))
    if not events:
        raise ValueError("Custodian response contained neither JSON nor SSE data")
    return events[-1]


def call_custodian(tool_name: str, arguments: dict) -> dict:
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
        "id": 1,
    }).encode()
    request = urllib.request.Request(
        CUSTODIAN_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/json, text/event-stream",
            **({"Mcp-Session-Id": SESSION_ID} if SESSION_ID else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return parse_response(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Custodian returned HTTP {error.code}: {detail}") from error


def initialize_session() -> None:
    global SESSION_ID
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "armada-instruction-cache", "version": "1.0"},
        },
        "id": 0,
    }).encode()
    request = urllib.request.Request(
        CUSTODIAN_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/json, text/event-stream",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        parse_response(response.read())
        SESSION_ID = response.headers["Mcp-Session-Id"]


def tool_result(response: dict) -> object:
    result = response.get("result", {})
    content = result.get("content") if isinstance(result, dict) else None
    if not content:
        return result
    texts = [block["text"] for block in content if block.get("type") == "text"]
    if len(texts) == 1:
        try:
            return json.loads(texts[0])
        except json.JSONDecodeError:
            return texts[0]
    return texts


def main() -> None:
    initialize_session()
    query = (
        "SELECT id FROM agent_instructions WHERE status = 'open' "
        "AND agent_name = 'brand-outreach-worker' "
        "AND CAST(REPLACE(id, 'AI-', '') AS INTEGER) BETWEEN 84925 AND 86468 "
        "ORDER BY CAST(REPLACE(id, 'AI-', '') AS INTEGER)"
    )
    rows = tool_result(call_custodian("armada_query", {"sql": query, "max_rows": 700}))
    if isinstance(rows, dict):
        rows = rows.get("rows", rows.get("data", []))
    if not isinstance(rows, list):
        raise ValueError(f"Unexpected instruction-query result: {rows!r}")

    ids = [row["id"] for row in rows]
    print(f"Found {len(ids)} open instructions")
    instructions = {}
    failures = []
    for number, ai_id in enumerate(ids, start=1):
        if number == 1 or number % 50 == 0:
            print(f"Fetching {number}/{len(ids)}")
        try:
            instructions[ai_id] = tool_result(call_custodian("get_agent_instruction", {"ai_id": ai_id}))
        except Exception as error:
            failures.append(f"{ai_id}: {error}")
            print(f"FAILED {failures[-1]}")

    OUTPUT.write_text(json.dumps(instructions), encoding="utf-8")
    print(f"Wrote {len(instructions)} instructions to {OUTPUT}")
    if failures:
        raise SystemExit(f"Failed to fetch {len(failures)} instructions")


if __name__ == "__main__":
    main()
