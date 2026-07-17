#!/usr/bin/env python3
"""Interactive launcher for Armada foreman flights on this Mac."""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ARMADA_DIR = Path("~/armada").expanduser()
NODE_DIR = ARMADA_DIR / "node-mcp-server"
NODE_SERVER = NODE_DIR / "server.py"
MCP_URL = os.environ.get("CUSTODIAN_MCP_URL", "https://custodian.lamannalogistics.com/mcp")
AUTH_PATH = Path(os.environ.get("CUSTODIAN_MCP_AUTH_PATH", "~/.local/share/opencode/mcp-auth.json")).expanduser()
FOREMAN_PROMPT = "You are an Armada foreman coordinating a fixed range of brand-outreach workers."
FOREMAN_MODEL = "deepseek/deepseek-v4-flash"
FOREMAN_IDS = re.compile(r"^AI-\d+$")


def load_token() -> str:
    token = os.environ.get("CUSTODIAN_MCP_TOKEN") or os.environ.get("BRIDGE_TOKEN", "")
    if token:
        return token
    try:
        entries = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to read Custodian OAuth credentials from {AUTH_PATH}: {exc}") from exc
    for entry in entries.values():
        token = entry.get("tokens", {}).get("accessToken")
        if token:
            return str(token)
    raise RuntimeError("Custodian OAuth access token is missing")


def parse_response(text: str) -> Any:
    if not text.strip():
        return {}
    events = [line[5:].strip() for line in text.splitlines() if line.startswith("data:")]
    return json.loads(events[-1] if events else text)


class CustodianClient:
    def __init__(self) -> None:
        self.token = load_token()
        self.session_id: str | None = None

    def post(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        try:
            response = requests.post(MCP_URL, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException as exc:
            detail = exc.response.text[:200] if exc.response is not None else str(exc)
            raise RuntimeError(f"Custodian request failed: {detail}") from exc
        session_id = response.headers.get("Mcp-Session-Id")
        if session_id:
            self.session_id = session_id
        return parse_response(response.text)

    def initialize(self) -> None:
        if self.session_id:
            return
        response = self.post({
            "jsonrpc": "2.0",
            "id": "armada-launcher-init",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "armada-launcher", "version": "1.0"},
            },
        })
        if response.get("error") or not self.session_id:
            raise RuntimeError(f"Custodian initialize failed: {response}")
        self.post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    def tool(self, name: str, arguments: dict[str, Any]) -> Any:
        self.initialize()
        response = self.post({
            "jsonrpc": "2.0",
            "id": f"armada-launcher-{int(time.time() * 1000)}",
            "method": "tools/call",
            "params": {"name": name, "arguments": {**arguments, "override_governance": False}},
        })
        if response.get("error"):
            raise RuntimeError(f"Custodian {name} failed: {response['error']}")
        content = response.get("result", {}).get("content", [])
        for block in content:
            if block.get("type") == "text":
                return json.loads(block["text"])
        return response.get("result", {})

    def query(self, sql: str) -> list[dict[str, Any]]:
        result = self.tool("armada_query", {"sql": sql, "max_rows": 5000})
        return result.get("rows", [])


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def node_python() -> str:
    virtualenv_python = NODE_DIR / ".venv/bin/python"
    return str(virtualenv_python if virtualenv_python.exists() else Path(sys.executable))


def node_running() -> bool:
    return subprocess.run(["pgrep", "-f", "[s]erver.py"], stdout=subprocess.DEVNULL).returncode == 0


def ensure_node_server() -> bool:
    if node_running():
        return True
    log = open("/tmp/node-mcp-server.log", "ab")
    subprocess.Popen(
        [node_python(), str(NODE_SERVER)], cwd=NODE_DIR, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    time.sleep(1)
    return node_running()


def open_workers(client: CustodianClient) -> list[str]:
    rows = client.query(
        "SELECT id FROM agent_instructions "
        "WHERE agent_name = 'brand-outreach-worker' AND status = 'open' ORDER BY id"
    )
    return [row["id"] for row in rows]


def split_evenly(items: list[str], groups: int) -> list[list[str]]:
    base, remainder = divmod(len(items), groups)
    return [items[index * base + min(index, remainder):(index + 1) * base + min(index + 1, remainder)] for index in range(groups)]


def foreman_body(dispatch_id: str, port: int, worker_ids: list[str]) -> str:
    return (
        "# Armada Foreman\n\n"
        f"Dispatch ID: {dispatch_id}\n"
        f"CDP port assignment: {port}\n"
        f"Model: {FOREMAN_MODEL}\n"
        f"Worker count: {len(worker_ids)}\n\n"
        "DO NOT stop until every worker ID in your list has been dispatched. Your context window is large enough "
        "for all workers. Stopping before completion is a failure - process ALL batches.\n\n"
        "Execute only these worker instruction IDs, in the stated order:\n"
        + "\n".join(worker_ids)
    )


def fly(client: CustodianClient) -> None:
    if not ensure_node_server():
        print("Warning: no persistent Node MCP process was detected; sync-from-custodian still runs directly.")
    workers = open_workers(client)
    print(f"{len(workers)} open workers ready")
    if not workers:
        return
    raw_groups = input("How many foremen? [4]: ").strip() or "4"
    try:
        groups = int(raw_groups)
    except ValueError as exc:
        raise RuntimeError("Foreman count must be an integer from 1 to 4") from exc
    if not 1 <= groups <= 4:
        raise RuntimeError("Foreman count must be from 1 to 4")

    dispatch_id = f"D-FLY-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    assignments = split_evenly(workers, groups)
    client.tool("armada_dispatch", {
        "dispatch_id": dispatch_id,
        "total_instructions": len(workers),
        "pool_size": groups,
        "model": FOREMAN_MODEL,
        "node_assignments": {f"F{index + 1}": len(worker_ids) for index, worker_ids in enumerate(assignments)},
    })
    for start in range(0, len(workers), 100):
        worker_ids = workers[start:start + 100]
        values = ", ".join(sql_quote(worker_id) for worker_id in worker_ids)
        client.tool("armada_query", {
            "sql": "UPDATE agent_instructions SET dispatch_id = "
            f"{sql_quote(dispatch_id)} WHERE id IN ({values})",
        })
    foremen: list[tuple[str, int, int]] = []
    for index, worker_ids in enumerate(assignments):
        result = client.tool("submit_agent_instruction", {
            "agent_name": "armada-foreman",
            "instruction": foreman_body(dispatch_id, 9222 + index, worker_ids),
            "model_override": FOREMAN_MODEL,
            "dispatch_id": dispatch_id,
        })
        foreman_id = result.get("id") or result.get("ai_id")
        if not foreman_id:
            raise RuntimeError(f"Custodian did not return a foreman ID: {result}")
        foremen.append((str(foreman_id), 9222 + index, len(worker_ids)))
    run_sync("--sync-from-custodian", dispatch_id=dispatch_id)
    print("\nForemen created:")
    for index, (foreman_id, port, count) in enumerate(foremen, start=1):
        print(f"F{index}: {foreman_id} (CDP {port}, {count} workers)")
    print("\nLaunch in separate terminals:")
    for _ in foremen:
        print(f"opencode --agent armada-foreman --model {FOREMAN_MODEL}")


def run_sync(flag: str, dispatch_id: str | None = None) -> dict[str, Any]:
    command = [node_python(), str(NODE_SERVER), flag]
    if dispatch_id is not None:
        command.extend(["--dispatch", dispatch_id])
    result = subprocess.run(command, cwd=NODE_DIR, text=True, capture_output=True, check=False)
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if result.returncode:
        raise RuntimeError(f"Node sync failed ({result.returncode}): {result.stdout.strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Unexpected node sync output: {result.stdout!r}") from exc


def latest_fly_foremen(client: CustodianClient) -> list[dict[str, Any]]:
    dispatches = client.query("SELECT dispatch_id FROM armada_dispatches WHERE dispatch_id LIKE 'D-FLY-%' ORDER BY created_at DESC LIMIT 1")
    if not dispatches:
        return []
    dispatch_id = sql_quote(dispatches[0]["dispatch_id"])
    return client.query(
        "SELECT id, instruction_body FROM agent_instructions "
        f"WHERE dispatch_id = {dispatch_id} AND agent_name = 'armada-foreman' ORDER BY id"
    )


def workers_from_foremen(foremen: list[dict[str, Any]]) -> list[str]:
    return sorted({line.strip() for foreman in foremen for line in foreman["instruction_body"].splitlines() if FOREMAN_IDS.fullmatch(line.strip())})


def mark_workers_executed(client: CustodianClient, worker_ids: list[str]) -> int:
    marked = 0
    for start in range(0, len(worker_ids), 100):
        batch = worker_ids[start:start + 100]
        values = ", ".join(sql_quote(worker_id) for worker_id in batch)
        open_count = client.query(
            "SELECT COUNT(*) AS count FROM agent_instructions "
            f"WHERE id IN ({values}) AND status = 'open'"
        )[0]["count"]
        if open_count:
            client.tool("armada_query", {
                "sql": "UPDATE agent_instructions SET status = 'executed', executed_at = CURRENT_TIMESTAMP "
                f"WHERE id IN ({values}) AND status = 'open'",
            })
            marked += open_count
    return marked


def accessible_count(client: CustodianClient) -> int | str:
    result = client.tool("call_project_tool", {
        "project": "fba-command-center",
        "tool_name": "fba_query",
        "params": {"sql": "SELECT COUNT(*) AS count FROM fba.artifact WHERE category = 'outreach_intel' AND status = 'ACCESSIBLE'"},
    })
    rows = result.get("result", result).get("rows", [])
    return rows[0]["count"] if rows else "unavailable"


def sync(client: CustodianClient) -> None:
    sync_result = run_sync("--sync-to-custodian")
    workers = workers_from_foremen(latest_fly_foremen(client))
    marked = mark_workers_executed(client, workers) if workers else 0
    print(f"Verdicts synced: {sync_result.get('synced_verdicts', 0)}")
    print(f"Workers marked executed: {marked}")
    print(f"Remaining open workers: {len(open_workers(client))}")
    print(f"ACCESSIBLE artifacts: {accessible_count(client)}")


def cdp_port_status(port: int) -> str:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return "listening"
    except OSError:
        return "down"


def status(client: CustodianClient) -> None:
    worker_count = len(open_workers(client))
    foreman_rows = client.query("SELECT COUNT(*) AS count FROM agent_instructions WHERE agent_name = 'armada-foreman' AND status = 'open'")
    artifact_counts = client.tool("call_project_tool", {
        "project": "fba-command-center",
        "tool_name": "fba_query",
        "params": {"sql": "SELECT status, COUNT(*) AS count FROM fba.artifact WHERE category = 'outreach_intel' AND status IN ('ACCESSIBLE', 'MAYBE', 'INCONCLUSIVE') GROUP BY status ORDER BY status"},
    })
    rows = artifact_counts.get("result", artifact_counts).get("rows", [])
    counts = {row["status"]: row["count"] for row in rows}
    print("Armada status")
    print(f"Open workers: {worker_count}")
    print(f"Open foremen: {foreman_rows[0]['count']}")
    print("Artifacts: " + ", ".join(f"{name}={counts.get(name, 0)}" for name in ("ACCESSIBLE", "MAYBE", "INCONCLUSIVE")))
    print(f"Node MCP: {'running' if node_running() else 'not detected'}")
    print("CDP ports: " + ", ".join(f"{port} {cdp_port_status(port)}" for port in range(9222, 9226)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=("fly", "sync", "status"))
    initial_command = parser.parse_args().command
    client = CustodianClient()
    dispatch = {"fly": fly, "sync": sync, "status": status}
    first = True
    while True:
        try:
            if first and initial_command:
                command = initial_command
            else:
                print()
                command = input("Command [fly/sync/status/quit]: ").strip().lower()
            first = False
            if command in ("quit", "exit", "q"):
                break
            if command not in dispatch:
                print("Choose fly, sync, status, or quit")
                continue
            dispatch[command](client)
        except KeyboardInterrupt:
            print()
            break
        except EOFError:
            break


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
