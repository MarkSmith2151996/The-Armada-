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
from datetime import datetime, timedelta, timezone
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
                text = block["text"]
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"text": text}
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
        "WHERE agent_name = 'brand-outreach-worker' AND status = 'FBA_READY' ORDER BY id"
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
    print(f"{len(workers)} FBA-ready workers")
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
    run_sync("--sync-from-custodian", instruction_type="FBA_READY")
    for start in range(0, len(workers), 100):
        worker_ids = workers[start:start + 100]
        values = ", ".join(sql_quote(worker_id) for worker_id in worker_ids)
        client.tool("armada_query", {
            "sql": "UPDATE agent_instructions SET dispatch_id = "
            f"{sql_quote(dispatch_id)}, status = 'dispatched' "
            f"WHERE id IN ({values}) AND status = 'FBA_READY'",
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
    run_sync("--sync-from-custodian", dispatch_id=dispatch_id, instruction_type="open")
    print("\nForemen created:")
    for index, (foreman_id, port, count) in enumerate(foremen, start=1):
        print(f"F{index}: {foreman_id} (CDP {port}, {count} workers)")
    print("\nLaunch in separate terminals:")
    for foreman_id, _, _ in foremen:
        print(f"opencode --agent armada-foreman --model {FOREMAN_MODEL} --prompt 'Execute {foreman_id}'")


def run_sync(
    flag: str,
    dispatch_id: str | None = None,
    instruction_type: str | None = None,
) -> dict[str, Any]:
    command = [node_python(), str(NODE_SERVER), flag]
    if instruction_type is not None:
        command.extend(["--type", instruction_type])
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
        dispatched_count = client.query(
            "SELECT COUNT(*) AS count FROM agent_instructions "
            f"WHERE id IN ({values}) AND status = 'dispatched'"
        )[0]["count"]
        if dispatched_count:
            client.tool("armada_query", {
                "sql": "UPDATE agent_instructions SET status = 'executed', executed_at = CURRENT_TIMESTAMP "
                f"WHERE id IN ({values}) AND status = 'dispatched'",
            })
            marked += dispatched_count
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
    print(f"Remaining FBA-ready workers: {len(open_workers(client))}")
    print(f"ACCESSIBLE artifacts: {accessible_count(client)}")


def cdp_port_status(port: int) -> str:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return "listening"
    except OSError:
        return "down"


def sqld_query(sql: str) -> list[dict[str, Any]]:
    """Run a read-only sqld query through its local HTTP endpoint."""
    response = requests.post(
        os.environ.get("SQLD_URL", "http://127.0.0.1:8400").rstrip("/") + "/v2/pipeline",
        json={"requests": [{"type": "execute", "stmt": {"sql": sql}}]},
        timeout=5,
    )
    response.raise_for_status()
    result = response.json().get("results", [{}])[0]
    if result.get("type") == "error":
        raise RuntimeError(result.get("error", {}).get("message", "sqld query failed"))
    payload = result.get("response", {}).get("result", {})
    columns = [column["name"] for column in payload.get("cols", [])]
    return [dict(zip(columns, [sqld_value(value) for value in row])) for row in payload.get("rows", [])]


def sqld_value(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    if value.get("type") == "null":
        return None
    raw = value.get("value")
    if value.get("type") == "integer" and raw is not None:
        return int(raw)
    if value.get("type") == "float" and raw is not None:
        return float(raw)
    return raw


def created_within_last_day(value: Any) -> bool:
    if not value:
        return False
    try:
        created_at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return created_at >= datetime.now(timezone.utc) - timedelta(days=1)


def serper_key_status() -> tuple[int, str]:
    key_path = NODE_DIR / "search_keys.json"
    try:
        payload = json.loads(key_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return 0, f"not configured ({key_path} is missing)"
    except (OSError, json.JSONDecodeError) as exc:
        return 0, f"invalid configuration: {exc}"

    configured = payload.get("keys", [])
    if not isinstance(configured, list):
        return 0, "invalid configuration: keys must be a list"
    usable = [
        item
        for item in configured
        if isinstance(item, dict)
        and item.get("provider") == "serper"
        and all(isinstance(item.get(field), str) and item[field] for field in ("key", "endpoint"))
    ]
    if not usable:
        return len(configured), "no Serper keys to test"

    failures: list[str] = []
    for index, key in enumerate(usable, start=1):
        try:
            response = requests.post(
                key["endpoint"],
                json={"q": "test", "num": 1},
                headers={"X-API-KEY": key["key"], "Content-Type": "application/json"},
                timeout=5,
            )
        except requests.RequestException as exc:
            failures.append(str(exc))
            continue
        if response.status_code == 200:
            return len(configured), f"valid (Serper key {index}/{len(usable)}, HTTP 200)"
        failures.append(f"HTTP {response.status_code}")
    return len(configured), f"test failed ({', '.join(failures)})"


def diagnose() -> None:
    """Print a non-mutating readiness report for an Armada flight."""
    print("Armada flight diagnostic")
    print(f"Generated: {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%SZ}")

    client: CustodianClient | None = None
    worker_rows: list[dict[str, Any]] = []
    foreman_rows: list[dict[str, Any]] = []
    custodian_error = ""
    try:
        client = CustodianClient()
        client.query("SELECT 1 AS ready")
        worker_rows = client.query(
            "SELECT id, created_at FROM agent_instructions "
            "WHERE agent_name = 'brand-outreach-worker' AND status = 'FBA_READY' ORDER BY created_at, id"
        )
        foreman_rows = client.query(
            "SELECT id, created_at FROM agent_instructions "
            "WHERE agent_name = 'armada-foreman' AND status = 'open' ORDER BY created_at, id"
        )
    except Exception as exc:
        custodian_error = str(exc)

    print("\nFBA-ready workers")
    if custodian_error:
        print("  Unavailable: Custodian query failed")
    else:
        print(f"  Total: {len(worker_rows)}")
        print(f"  Oldest: {worker_rows[0].get('created_at') if worker_rows else 'n/a'}")
        print(f"  Newest: {worker_rows[-1].get('created_at') if worker_rows else 'n/a'}")
        print(f"  Created in last 24h: {sum(created_within_last_day(row.get('created_at')) for row in worker_rows)}")

    print("\nCustodian connectivity")
    print(f"  MCP read query: {'OK' if not custodian_error else 'FAILED: ' + custodian_error}")

    sqld_process = subprocess.run(["pgrep", "-f", "[s]qld"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    sqld_error = ""
    sqld_reachable = False
    sqld_total: int | None = None
    unsynced_verdicts: int | None = None
    local_executed: list[dict[str, Any]] = []
    unresolved_escalations: list[dict[str, Any]] | None = None
    try:
        sqld_total = int(sqld_query("SELECT COUNT(*) AS count FROM instructions")[0]["count"])
        unsynced_verdicts = int(sqld_query("SELECT COUNT(*) AS count FROM verdicts WHERE synced_at IS NULL")[0]["count"])
        local_executed = sqld_query(
            "SELECT id FROM instructions WHERE agent_name = 'brand-outreach-worker' AND status = 'executed'"
        )
        sqld_reachable = True
        try:
            unresolved_escalations = sqld_query(
                "SELECT foreman_id, failure_reason, workers_remaining FROM escalations "
                "WHERE synced_at IS NULL ORDER BY created_at"
            )
        except Exception:
            unresolved_escalations = None
    except Exception as exc:
        sqld_error = str(exc)

    print("\nsqld state")
    print(f"  Process: {'running' if sqld_process else 'not detected'}")
    if sqld_reachable:
        print(f"  Instructions: {sqld_total}")
        print(f"  Unsynced verdicts: {unsynced_verdicts}")
    else:
        print(f"  Query: FAILED: {sqld_error}")

    cdp_ports = {port: cdp_port_status(port) for port in range(9222, 9226)}
    print("\nCDP ports")
    print("  " + ", ".join(f"{port} {state}" for port, state in cdp_ports.items()))

    node_is_running = node_running()
    print("\nNode MCP server")
    print(f"  {'running' if node_is_running else 'not detected'}")

    key_count, serper_status = serper_key_status()
    serper_valid = serper_status.startswith("valid ")
    print("\nSerper keys")
    print(f"  Configured: {key_count}")
    print(f"  Test: {serper_status}")

    print("\nOpen foremen")
    if custodian_error:
        print("  Unavailable: Custodian query failed")
    elif foreman_rows:
        for row in foreman_rows:
            print(f"  {row.get('id')}: {row.get('created_at')}")
    else:
        print("  None")

    unreconciled: list[str] = []
    if not custodian_error and sqld_reachable:
        remote_open_ids = {str(row["id"]) for row in worker_rows}
        unreconciled = [str(row["id"]) for row in local_executed if str(row["id"]) in remote_open_ids]
    print("\nUnreconciled workers")
    if custodian_error or not sqld_reachable:
        print("  Unavailable: requires Custodian and sqld")
    elif unreconciled:
        print("  " + ", ".join(unreconciled))
    else:
        print("  None")

    print("\nEscalation records")
    if unresolved_escalations is None:
        print("  None or table not initialized")
    elif not unresolved_escalations:
        print("  None")
    else:
        for escalation in unresolved_escalations:
            try:
                remaining_count = len(json.loads(escalation.get("workers_remaining") or "[]"))
            except json.JSONDecodeError:
                remaining_count = "unknown"
            print(
                f"  {escalation.get('foreman_id')}: {escalation.get('failure_reason')} "
                f"({remaining_count} workers remaining)"
            )

    print("\nAuto-creation pipeline")
    print("  WSL services not checkable from Mac.")

    critical: list[str] = []
    attention: list[str] = []
    if custodian_error:
        critical.append("Custodian connectivity failed")
    elif not worker_rows:
        critical.append("no FBA-ready workers")
    if not sqld_process:
        critical.append("sqld process is not running")
    if not sqld_reachable:
        critical.append("sqld read query failed")
    if not node_is_running:
        critical.append("Node MCP server is not running")
    down_ports = [str(port) for port, state in cdp_ports.items() if state != "listening"]
    if down_ports:
        critical.append("CDP ports down: " + ", ".join(down_ports))
    if not serper_valid:
        critical.append("Serper key validation failed")
    if foreman_rows:
        attention.append(f"{len(foreman_rows)} stale open foreman(s)")
    if unsynced_verdicts:
        attention.append(f"{unsynced_verdicts} unsynced verdict(s)")
    if unreconciled:
        attention.append(f"{len(unreconciled)} unreconciled worker(s)")
    if unresolved_escalations:
        attention.append(f"{len(unresolved_escalations)} unresolved escalation(s)")

    print("\nFlight recommendation")
    if critical:
        print("  BLOCKED: " + "; ".join(critical))
    elif attention:
        print("  ATTENTION: " + "; ".join(attention))
    else:
        print(f"  READY: {len(worker_rows)} FBA-ready workers, all systems green")


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
    print(f"FBA-ready workers: {worker_count}")
    print(f"Open foremen: {foreman_rows[0]['count']}")
    print("Artifacts: " + ", ".join(f"{name}={counts.get(name, 0)}" for name in ("ACCESSIBLE", "MAYBE", "INCONCLUSIVE")))
    print(f"Node MCP: {'running' if node_running() else 'not detected'}")
    print("CDP ports: " + ", ".join(f"{port} {cdp_port_status(port)}" for port in range(9222, 9226)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=("fly", "sync", "status", "diagnose"))
    initial_command = parser.parse_args().command
    dispatch = {"fly": fly, "sync": sync, "status": status}
    client: CustodianClient | None = None
    first = True
    while True:
        try:
            if first and initial_command:
                command = initial_command
            else:
                print()
                command = input("Command [fly/sync/status/diagnose/quit]: ").strip().lower()
            first = False
            if command in ("quit", "exit", "q"):
                break
            if command == "diagnose":
                diagnose()
                if initial_command:
                    return
                continue
            if command not in dispatch:
                print("Choose fly, sync, status, diagnose, or quit")
                continue
            client = client or CustodianClient()
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
