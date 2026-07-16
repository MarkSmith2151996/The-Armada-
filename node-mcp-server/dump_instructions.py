#!/usr/bin/env python3
import json, requests, sys

CUSTODIAN_URL = "http://100.95.20.98:8223/mcp"
TOKEN = "96b2acbc0ae6cb1597ce4c3998938d28b7e5f8805b51deb795afa815aa6b75df"

def call_tool(tool_name, params):
    resp = requests.post(CUSTODIAN_URL, json={
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": tool_name, "arguments": params}
    }, headers={
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    })
    result = resp.json().get("result", {})
    for block in result.get("content", []):
        if block.get("type") == "text":
            return json.loads(block["text"])
    return None

data = call_tool("armada_query", {
    "sql": "SELECT id, instruction_body FROM agent_instructions WHERE agent_name = 'brand-outreach-worker' AND status = 'open' ORDER BY id",
    "max_rows": 2000
})

if not data or "rows" not in data:
    print("ERROR: No data returned from Custodian", file=sys.stderr)
    sys.exit(1)

cache = {}
for row in data["rows"]:
    cache[row["id"]] = row["instruction_body"]

with open("instructions.json", "w") as f:
    json.dump(cache, f, indent=2)

print(f"Wrote {len(cache)} instructions to instructions.json")
