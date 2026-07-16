from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests

from config import Settings


_SESSION_ID: str | None = None


def _load_token() -> str:
    token = os.environ.get("CUSTODIAN_MCP_TOKEN") or os.environ.get("BRIDGE_TOKEN", "")
    if token:
        return token

    auth_path = Path(os.environ.get("CUSTODIAN_MCP_AUTH_PATH", "~/.local/share/opencode/mcp-auth.json")).expanduser()
    try:
        data = json.loads(auth_path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    for entry in data.values():
        token = entry.get("tokens", {}).get("accessToken")
        if token:
            return str(token)
    return ""


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    token = _load_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _parse_response(text: str) -> Any:
    if not text.strip():
        return None

    messages: list[dict[str, Any]] = []
    data_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("data:"):
            data_lines.append(line[5:].strip())
        elif not line.strip() and data_lines:
            messages.append(json.loads("\n".join(data_lines)))
            data_lines = []
    if data_lines:
        messages.append(json.loads("\n".join(data_lines)))
    if messages:
        return messages[-1]

    return json.loads(text)


def _post(settings: Settings, payload: dict[str, Any]) -> tuple[requests.Response, Any]:
    global _SESSION_ID

    headers = _headers()
    if _SESSION_ID:
        headers["Mcp-Session-Id"] = _SESSION_ID
    response = requests.post(
        settings.custodian_mcp_url,
        json=payload,
        headers=headers,
        timeout=settings.request_timeout_seconds,
    )
    session_id = response.headers.get("Mcp-Session-Id")
    if session_id:
        _SESSION_ID = session_id
    try:
        parsed: Any = _parse_response(response.text)
    except Exception:
        parsed = response.text[:2000]
    return response, parsed


def _ensure_session(settings: Settings) -> dict[str, Any] | None:
    global _SESSION_ID

    if _SESSION_ID:
        return None

    response, parsed = _post(
        settings,
        {
            "jsonrpc": "2.0",
            "id": "armada-node-init",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "armada-node-mcp", "version": "1.0"},
            },
        },
    )
    if not response.ok or (isinstance(parsed, dict) and parsed.get("error")):
        return {"ok": False, "status_code": response.status_code, "response": parsed, "stage": "initialize"}
    if not _SESSION_ID:
        return {"ok": False, "status_code": response.status_code, "response": parsed, "stage": "initialize", "error": "Missing Mcp-Session-Id"}

    response, parsed = _post(
        settings,
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
    )
    if not response.ok or (isinstance(parsed, dict) and parsed.get("error")):
        _SESSION_ID = None
        return {"ok": False, "status_code": response.status_code, "response": parsed, "stage": "initialized"}
    return None


def mark_agent_instruction_executed(
    *,
    settings: Settings,
    ai_id: str,
    notes: str,
    produced_files: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not ai_id:
        return {"ok": False, "skipped": True, "reason": "ai_id was empty"}

    payload = {
        "jsonrpc": "2.0",
        "id": f"armada-node-{int(time.time() * 1000)}",
        "method": "tools/call",
        "params": {
            "name": settings.custodian_mark_tool,
            "arguments": {
                "ai_id": ai_id,
                "notes": notes,
                "produced_files": produced_files or [],
                "override_governance": False,
            },
        },
    }
    try:
        session_error = _ensure_session(settings)
        if session_error:
            return session_error

        response, parsed = _post(settings, payload)
        return {
            "ok": response.ok and not (isinstance(parsed, dict) and parsed.get("error")),
            "status_code": response.status_code,
            "response": parsed,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "custodian_mcp_url": settings.custodian_mcp_url}


def call_tool(settings: Settings, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": f"armada-node-{tool_name}-{int(time.time() * 1000)}",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": {**arguments, "override_governance": False},
        },
    }
    try:
        session_error = _ensure_session(settings)
        if session_error:
            return session_error

        response, parsed = _post(settings, payload)
        return {
            "ok": response.ok and not (isinstance(parsed, dict) and parsed.get("error")),
            "status_code": response.status_code,
            "response": parsed,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "custodian_mcp_url": settings.custodian_mcp_url}


def upsert_flywheel_artifact(
    *,
    settings: Settings,
    brand_name: str,
    brand_slug: str,
    verdict: str,
    notes: str,
    ai_id: str,
    verdict_payload: dict[str, Any],
) -> dict[str, Any]:
    return call_tool(
        settings,
        "call_project_tool",
        {
            "project": "fba-command-center",
            "tool_name": "upsert_flywheel_artifact",
            "params": {
                "category": "outreach_intel",
                "subject": f"outreach:{brand_slug}",
                "title": f"{brand_name} - Outreach Intelligence",
                "summary": notes,
                "analysis": json.dumps(verdict_payload, ensure_ascii=True, sort_keys=True),
                "status": verdict,
                "source_task": ai_id,
                "metadata": verdict_payload,
            },
        },
    )
