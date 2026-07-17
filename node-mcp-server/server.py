#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from cdp_pool import ensure_initialized, pool
from mcp.server.fastmcp import FastMCP

from config import get_settings
from local_store import ContextStore
from tools.browse_page import handle_browse_page
from tools.custodian_client import call_tool
from tools.edge_store import SqldStore
from tools.get_context import handle_get_context
from tools.google_search import handle_google_search
from tools.record_verdict import handle_record_verdict
from tools.search_brand import handle_search_brand, serper_search as _serper_search


settings = get_settings()
store = ContextStore(settings)
mcp = FastMCP("armada-node-mcp")
INSTRUCTIONS_FILE = Path(__file__).parent / "instructions.json"
_instruction_cache: dict[str, Any] | None = None


def _load_instructions() -> dict[str, Any]:
    global _instruction_cache
    if _instruction_cache is None:
        with INSTRUCTIONS_FILE.open(encoding="utf-8") as file:
            _instruction_cache = json.load(file)
    return _instruction_cache


def _tool_content(result: dict[str, Any]) -> Any:
    response = result.get("response", {})
    content = response.get("result", {}).get("content", []) if isinstance(response, dict) else []
    for block in content:
        if block.get("type") == "text":
            text = block["text"]
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"text": text}
    return response


def _custodian_rows(sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
    arguments: dict[str, Any] = {"sql": sql, "max_rows": 2000}
    if params is not None:
        arguments["params"] = params
    result = call_tool(settings, "armada_query", arguments)
    if not result.get("ok"):
        raise RuntimeError(result.get("error") or str(result.get("response")))
    payload = _tool_content(result)
    rows = payload.get("rows", []) if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        raise RuntimeError(f"Unexpected Custodian result: {payload!r}")
    return rows


def _batches(items: list[tuple[str, list[Any]]], size: int = 100) -> list[list[tuple[str, list[Any]]]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def sync_from_custodian(dispatch_id: str | None = None) -> dict[str, int]:
    edge_store = SqldStore(settings)
    edge_store.ensure_schema()
    if dispatch_id is None:
        workers = _custodian_rows(
            "SELECT id, agent_name, instruction_body, status, dispatch_id, created_at "
            "FROM agent_instructions WHERE status = 'open' AND agent_name != 'armada-foreman' ORDER BY id"
        )
        foremen = _custodian_rows(
            "SELECT id, agent_name, instruction_body, status, dispatch_id, created_at "
            "FROM agent_instructions WHERE status = 'open' AND agent_name = 'armada-foreman' ORDER BY id"
        )
        dispatches = _custodian_rows(
            "SELECT dispatch_id, total_instructions, completed, failed, status, created_at FROM armada_dispatches ORDER BY dispatch_id"
        )
        local_open_workers = edge_store.query(
            "SELECT id FROM instructions WHERE status = 'open' AND agent_name != 'armada-foreman'"
        )
    else:
        workers = _custodian_rows(
            "SELECT id, agent_name, instruction_body, status, dispatch_id, created_at "
            "FROM agent_instructions WHERE status = 'open' AND agent_name != 'armada-foreman' AND dispatch_id = ? ORDER BY id",
            [dispatch_id],
        )
        foremen = _custodian_rows(
            "SELECT id, agent_name, instruction_body, status, dispatch_id, created_at "
            "FROM agent_instructions WHERE status = 'open' AND agent_name = 'armada-foreman' AND dispatch_id = ? ORDER BY id",
            [dispatch_id],
        )
        dispatches = _custodian_rows(
            "SELECT dispatch_id, total_instructions, completed, failed, status, created_at "
            "FROM armada_dispatches WHERE dispatch_id = ?",
            [dispatch_id],
        )
        local_open_workers = edge_store.query(
            "SELECT id FROM instructions WHERE status = 'open' AND agent_name != 'armada-foreman' AND dispatch_id = ?",
            [dispatch_id],
        )
    remote_worker_ids = {instruction["id"] for instruction in workers}
    stale_worker_ids = [row["id"] for row in local_open_workers if row["id"] not in remote_worker_ids]
    for stale_batch in [stale_worker_ids[index : index + 500] for index in range(0, len(stale_worker_ids), 500)]:
        placeholders = ", ".join("?" for _ in stale_batch)
        edge_store.execute(f"DELETE FROM instructions WHERE id IN ({placeholders})", stale_batch)
    instruction_writes = []
    for instruction in [*workers, *foremen]:
        instruction_writes.append((
            """
            INSERT INTO instructions (id, agent_name, instruction_body, status, dispatch_id, created_at, status_synced_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                agent_name = excluded.agent_name,
                instruction_body = excluded.instruction_body,
                status = excluded.status,
                dispatch_id = excluded.dispatch_id,
                created_at = excluded.created_at,
                updated_at = datetime('now'),
                status_synced_at = datetime('now')
            """,
            [
                instruction["id"],
                instruction["agent_name"],
                instruction["instruction_body"],
                instruction["status"],
                instruction.get("dispatch_id"),
                instruction.get("created_at"),
            ],
        ))
    for batch in _batches(instruction_writes):
        edge_store.execute_many(batch)
    dispatch_writes = []
    for dispatch in dispatches:
        dispatch_writes.append((
            """
            INSERT INTO dispatches (dispatch_id, total_instructions, completed, failed, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(dispatch_id) DO UPDATE SET
                total_instructions = excluded.total_instructions,
                completed = excluded.completed,
                failed = excluded.failed,
                status = excluded.status,
                created_at = excluded.created_at,
                updated_at = datetime('now')
            """,
            [
                dispatch["dispatch_id"],
                dispatch.get("total_instructions"),
                dispatch.get("completed", 0),
                dispatch.get("failed", 0),
                dispatch.get("status", "active"),
                dispatch.get("created_at"),
            ],
        ))
    for batch in _batches(dispatch_writes):
        edge_store.execute_many(batch)
    return {"instructions": len(workers) + len(foremen), "workers": len(workers), "foremen": len(foremen), "dispatches": len(dispatches)}


def sync_to_custodian() -> dict[str, int]:
    edge_store = SqldStore(settings)
    edge_store.ensure_schema()
    verdicts = edge_store.query("SELECT id, raw_payload FROM verdicts WHERE synced_at IS NULL ORDER BY id")
    # Keep a stalled remote request from blocking the entire durable queue.
    sync_settings = replace(settings, request_timeout_seconds=10)
    synced_verdicts = 0
    failed_verdicts = 0
    for row in verdicts:
        payload = json.loads(row["raw_payload"])
        result = call_tool(
            sync_settings,
            "call_project_tool",
            {
                "project": "fba-command-center",
                "tool_name": "upsert_flywheel_artifact",
                "params": {
                    "category": "outreach_intel",
                    "subject": f"outreach:{payload['brand_slug']}",
                    "title": f"{payload['brand_name']} - Outreach Intelligence",
                    "summary": payload["notes"],
                    "analysis": json.dumps(payload, ensure_ascii=True, sort_keys=True),
                    "status": payload["verdict"],
                    "source_task": payload["ai_id"],
                    "metadata": payload,
                },
            },
        )
        response = result.get("response")
        print(
            json.dumps(
                {
                    "sync_attempt": "verdict",
                    "verdict_id": row["id"],
                    "brand_slug": payload.get("brand_slug"),
                    "status_code": result.get("status_code"),
                    "response_preview": str(response)[:100],
                },
                ensure_ascii=True,
                default=str,
            ),
            file=sys.stderr,
        )
        if result.get("ok"):
            edge_store.execute("UPDATE verdicts SET synced_at = datetime('now') WHERE id = ?", [row["id"]])
            synced_verdicts += 1
        else:
            failed_verdicts += 1
            print(
                json.dumps(
                    {
                        "sync_failure": "verdict",
                        "verdict_id": row["id"],
                        "brand_slug": payload.get("brand_slug"),
                        "error": result.get("error"),
                        "status_code": result.get("status_code"),
                        "stage": result.get("stage"),
                        "response": result.get("response"),
                    },
                    ensure_ascii=True,
                    default=str,
                ),
                file=sys.stderr,
            )
    statuses = edge_store.query(
        "SELECT id, status FROM instructions WHERE status != 'open' AND status_synced_at IS NULL ORDER BY id"
    )
    synced_statuses = 0
    failed_statuses = 0
    for instruction in statuses:
        result = call_tool(
            sync_settings,
            "armada_query",
            {"sql": "UPDATE agent_instructions SET status = ? WHERE id = ?", "params": [instruction["status"], instruction["id"]]},
        )
        if result.get("ok"):
            edge_store.execute(
                "UPDATE instructions SET status_synced_at = datetime('now') WHERE id = ?", [instruction["id"]]
            )
            synced_statuses += 1
        else:
            failed_statuses += 1
            print(
                json.dumps(
                    {
                        "sync_failure": "instruction_status",
                        "instruction_id": instruction["id"],
                        "status": instruction["status"],
                        "error": result.get("error"),
                        "status_code": result.get("status_code"),
                        "stage": result.get("stage"),
                        "response": result.get("response"),
                    },
                    ensure_ascii=True,
                    default=str,
                ),
                file=sys.stderr,
            )
    return {
        "synced_verdicts": synced_verdicts,
        "failed_verdicts": failed_verdicts,
        "synced_statuses": synced_statuses,
        "failed_statuses": failed_statuses,
    }


def serper_search(query: str, num_results: int = 10) -> list[dict[str, str]]:
    """Run the configured Serper-compatible search API."""
    results, _ = _serper_search(settings, query, num_results)
    return results


@mcp.tool()
def search_brand(brand_name: str, query: str, session_id: str = "", ai_id: str = "") -> dict[str, Any]:
    """Search the web for brand sourcing evidence; stores full SearXNG results locally and returns top 3 snippets."""
    return handle_search_brand(
        settings=settings,
        store=store,
        brand_name=brand_name,
        query=query,
        session_id=session_id,
        ai_id=ai_id,
    )


@mcp.tool()
def google_search(query: str, cdp_port: int | None = None) -> dict[str, Any]:
    """Search Google through Chrome CDP and return up to 10 organic results."""
    return handle_google_search(settings=settings, store=store, query=query, cdp_port=cdp_port)


@mcp.tool()
async def browse_page(
    url: str,
    task: str = "Extract wholesale, dealer, distributor, contact, Faire, and Amazon marketplace restriction evidence.",
    cdp_port: int | None = None,
    session_id: str = "",
    brand_name: str = "",
    ai_id: str = "",
) -> dict[str, Any]:
    """Browse a URL through the local Chrome CDP accessibility tree and store the full snapshot in the context DB."""
    return await handle_browse_page(
        settings=settings,
        store=store,
        url=url,
        task=task,
        cdp_port=cdp_port,
        session_id=session_id,
        brand_name=brand_name,
        ai_id=ai_id,
    )


@mcp.tool()
def acquire_cdp() -> dict[str, Any]:
    """Acquire a dedicated, headless Chrome CDP port for one worker."""
    ensure_initialized()
    return pool.acquire()


@mcp.tool()
def cleanup_cdp(cdp_port: int) -> dict[str, Any]:
    """Close all tabs on a Chrome CDP instance without releasing the slot."""
    ensure_initialized()
    return pool.cleanup(cdp_port)


@mcp.tool()
def release_cdp(port: int) -> dict[str, Any]:
    """Release a Chrome CDP port without stopping its Chrome process."""
    ensure_initialized()
    return pool.release(port)


@mcp.tool()
def get_context(query: str, session_id: str, limit: int = 3) -> dict[str, Any]:
    """Retrieve previously sandboxed tool results for this worker session using local FTS search."""
    return handle_get_context(store=store, query=query, session_id=session_id, limit=limit)


@mcp.tool()
def get_instruction(ai_id: str) -> dict[str, Any]:
    """Retrieve an instruction from local sqld, falling back to instructions.json if needed."""
    try:
        rows = SqldStore(settings).query("SELECT * FROM instructions WHERE id = ?", [ai_id])
    except Exception as exc:
        rows = []
        sqld_error = str(exc)
    else:
        sqld_error = ""
    if rows:
        return rows[0]
    instruction = _load_instructions().get(ai_id)
    if instruction is None:
        error = f"Instruction {ai_id} was not found in local sqld or the fallback cache"
        return {"error": error, "sqld_error": sqld_error} if sqld_error else {"error": error}
    if isinstance(instruction, dict):
        return instruction
    return {"id": ai_id, "instruction_body": instruction}


@mcp.tool()
def record_verdict(
    brand_name: str,
    brand_slug: str,
    verdict: str,
    confidence: str = "",
    wholesale_url: str = "",
    restrictions: str = "",
    distributor: str = "",
    contact_method: str = "none",
    notes: str = "",
    ai_id: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    """Queue a research verdict in local sqld for post-flight synchronization."""
    return handle_record_verdict(
        settings=settings,
        brand_name=brand_name,
        brand_slug=brand_slug,
        verdict=verdict,
        confidence=confidence,
        wholesale_url=wholesale_url,
        restrictions=restrictions,
        distributor=distributor,
        contact_method=contact_method,
        notes=notes,
        ai_id=ai_id,
        session_id=session_id,
    )


@mcp.tool()
def list_open_instructions(dispatch_id: str) -> list[dict[str, Any]]:
    """List locally cached open instructions for a dispatch without a network request."""
    try:
        return SqldStore(settings).query(
            "SELECT id, status FROM instructions WHERE status = 'open' AND dispatch_id = ? ORDER BY id", [dispatch_id]
        )
    except Exception as exc:
        return [{"error": f"Local sqld read failed: {exc}"}]


@mcp.tool()
def mark_instruction_status(ai_id: str, status: str) -> dict[str, Any]:
    """Update an instruction's local flight status for post-flight synchronization."""
    if status not in {"open", "executing", "executed", "failed"}:
        return {"ok": False, "error": f"Invalid status {status!r}"}
    try:
        edge_store = SqldStore(settings)
        edge_store.execute(
            "UPDATE instructions SET status = ?, updated_at = datetime('now'), status_synced_at = NULL WHERE id = ?",
            [status, ai_id],
        )
        row = edge_store.query("SELECT id FROM instructions WHERE id = ?", [ai_id])
        return {"ok": bool(row), "id": ai_id, "status": status}
    except Exception as exc:
        return {"ok": False, "error": f"Local sqld write failed: {exc}"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--sync-from-custodian", action="store_true")
    group.add_argument("--sync-to-custodian", action="store_true")
    group.add_argument(
        "--daemon",
        action="store_true",
        help="serve MCP over HTTP so the process can run without a terminal",
    )
    parser.add_argument("--port", type=int, default=8401)
    parser.add_argument("--dispatch", help="sync only instructions and dispatch metadata for this dispatch ID")
    args = parser.parse_args()
    if args.sync_from_custodian:
        print(json.dumps(sync_from_custodian(dispatch_id=args.dispatch), sort_keys=True))
    elif args.sync_to_custodian:
        print(json.dumps(sync_to_custodian(), sort_keys=True))
    elif args.daemon:
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    else:
        mcp.run()
