from __future__ import annotations

import json
import threading
from typing import Any

import requests

from config import Settings


SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS instructions (
        id TEXT PRIMARY KEY,
        agent_name TEXT NOT NULL,
        instruction_body TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'open',
        dispatch_id TEXT,
        assigned_foreman TEXT,
        created_at TEXT,
        updated_at TEXT DEFAULT (datetime('now')),
        status_synced_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS verdicts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        instruction_id TEXT NOT NULL,
        brand_name TEXT NOT NULL,
        brand_slug TEXT NOT NULL,
        verdict TEXT NOT NULL,
        confidence TEXT NOT NULL,
        wholesale_url TEXT,
        restrictions TEXT,
        distributor TEXT,
        contact_method TEXT,
        notes TEXT,
        raw_payload TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        synced_at TEXT DEFAULT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS dispatches (
        dispatch_id TEXT PRIMARY KEY,
        total_instructions INTEGER,
        completed INTEGER DEFAULT 0,
        failed INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        created_at TEXT,
        updated_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS escalations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        foreman_id TEXT NOT NULL,
        dispatch_id TEXT,
        workers_completed TEXT,
        workers_remaining TEXT,
        failure_reason TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        synced_at TEXT DEFAULT NULL
    )
    """,
)
_schema_lock = threading.Lock()
_schema_ready = False


class SqldStore:
    def __init__(self, settings: Settings):
        self.url = settings.sqld_url.rstrip("/")
        self.timeout = settings.request_timeout_seconds

    def _request(self, sql: str, args: list[Any] | None = None) -> dict[str, Any]:
        statement: dict[str, Any] = {"sql": sql}
        if args:
            statement["args"] = [self._value(value) for value in args]
        response = requests.post(
            f"{self.url}/v2/pipeline",
            json={"requests": [{"type": "execute", "stmt": statement}]},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        result = payload.get("results", [{}])[0]
        if result.get("type") == "error":
            raise RuntimeError(result.get("error", {}).get("message", "sqld query failed"))
        return result.get("response", {}).get("result", {})

    @staticmethod
    def _value(value: Any) -> dict[str, Any]:
        if value is None:
            return {"type": "null"}
        if isinstance(value, bool):
            return {"type": "integer", "value": "1" if value else "0"}
        if isinstance(value, int):
            return {"type": "integer", "value": str(value)}
        if isinstance(value, float):
            return {"type": "float", "value": value}
        return {"type": "text", "value": str(value)}

    def ensure_schema(self) -> None:
        global _schema_ready
        if _schema_ready:
            return
        with _schema_lock:
            if _schema_ready:
                return
            for statement in SCHEMA:
                self.execute(statement)
            _schema_ready = True

    def execute(self, sql: str, args: list[Any] | None = None) -> dict[str, Any]:
        return self._request(sql, args)

    def execute_many(self, statements: list[tuple[str, list[Any]]]) -> None:
        requests_payload = []
        for sql, args in statements:
            requests_payload.append(
                {
                    "type": "execute",
                    "stmt": {"sql": sql, "args": [self._value(value) for value in args]},
                }
            )
        response = requests.post(
            f"{self.url}/v2/pipeline",
            json={"requests": requests_payload},
            timeout=self.timeout,
        )
        response.raise_for_status()
        for result in response.json().get("results", []):
            if result.get("type") == "error":
                raise RuntimeError(result.get("error", {}).get("message", "sqld batch write failed"))

    def query(self, sql: str, args: list[Any] | None = None) -> list[dict[str, Any]]:
        result = self._request(sql, args)
        columns = [column["name"] for column in result.get("cols", [])]
        return [
            dict(zip(columns, [self._decode_value(value) for value in row]))
            for row in result.get("rows", [])
        ]

    @staticmethod
    def _decode_value(value: Any) -> Any:
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

    def insert_verdict(self, payload: dict[str, Any]) -> None:
        self.execute(
            """
            INSERT INTO verdicts (
                instruction_id, brand_name, brand_slug, verdict, confidence, wholesale_url,
                restrictions, distributor, contact_method, notes, raw_payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                payload["ai_id"] or payload["session_id"] or payload["brand_slug"],
                payload["brand_name"],
                payload["brand_slug"],
                payload["verdict"],
                payload["confidence"],
                payload["wholesale_url"],
                payload["restrictions"],
                payload["distributor"],
                payload["contact_method"],
                payload["notes"],
                json.dumps(payload, ensure_ascii=True, sort_keys=True),
            ],
        )
