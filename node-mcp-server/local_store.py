from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from config import Settings


def estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / 4))


class ContextStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.settings.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.settings.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        schema_path = Path(__file__).resolve().parent / "schema.sql"
        with self._connect() as conn:
            conn.executescript(schema_path.read_text(encoding="utf-8"))

    def ensure_session(self, session_id: str, brand: str, ai_id: str) -> str:
        session_id = (session_id or ai_id or brand or "default").strip()
        brand = (brand or "unknown").strip()
        ai_id = (ai_id or session_id).strip()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO worker_sessions(session_id, brand, ai_id, node)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    brand = excluded.brand,
                    ai_id = excluded.ai_id,
                    node = excluded.node,
                    status = 'active'
                """,
                (session_id, brand, ai_id, self.settings.node_name),
            )
        return session_id

    def increment_turn(self, session_id: str, brand: str, ai_id: str) -> int:
        session_id = self.ensure_session(session_id, brand, ai_id)
        with self._connect() as conn:
            conn.execute(
                "UPDATE worker_sessions SET turn_count = turn_count + 1 WHERE session_id = ?",
                (session_id,),
            )
            row = conn.execute(
                "SELECT turn_count FROM worker_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return int(row["turn_count"] if row else 1)

    def add_tool_result(
        self,
        *,
        session_id: str,
        turn: int,
        tool_name: str,
        query: str,
        result_summary: str,
        full_result: Any,
    ) -> int:
        if isinstance(full_result, str):
            full_text = full_result
        else:
            full_text = json.dumps(full_result, ensure_ascii=True, sort_keys=True)
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO tool_results(session_id, turn, tool_name, query, result_summary, full_result, token_estimate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    turn,
                    tool_name,
                    query,
                    result_summary,
                    full_text,
                    estimate_tokens(full_text),
                ),
            )
            return int(cur.lastrowid)

    def search_context(self, session_id: str, query: str, limit: int = 3) -> list[dict[str, Any]]:
        terms = [part for part in query.replace('"', " ").split() if part]
        fts_query = " OR ".join(f'"{term}"' for term in terms) if terms else ""
        with self._connect() as conn:
            if fts_query:
                try:
                    rows = conn.execute(
                        """
                        SELECT r.id, r.turn, r.tool_name, r.query, r.result_summary, r.token_estimate,
                               substr(r.full_result, 1, 2000) AS full_result_preview
                        FROM tool_results_fts f
                        JOIN tool_results r ON r.id = f.rowid
                        WHERE tool_results_fts MATCH ? AND r.session_id = ?
                        ORDER BY bm25(tool_results_fts)
                        LIMIT ?
                        """,
                        (fts_query, session_id, limit),
                    ).fetchall()
                    return [dict(row) for row in rows]
                except sqlite3.OperationalError:
                    pass

            like = f"%{query}%"
            rows = conn.execute(
                """
                SELECT id, turn, tool_name, query, result_summary, token_estimate,
                       substr(full_result, 1, 2000) AS full_result_preview
                FROM tool_results
                WHERE session_id = ?
                  AND (query LIKE ? OR result_summary LIKE ? OR full_result LIKE ?)
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, like, like, like, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def telemetry(self, session_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            session = conn.execute(
                """
                SELECT session_id, brand, ai_id, node, turn_count, started_at,
                       COALESCE((julianday('now') - julianday(started_at)) * 86400.0, 0) AS duration_seconds
                FROM worker_sessions WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
            counts = conn.execute(
                """
                SELECT COUNT(*) AS tool_calls_count,
                       SUM(CASE WHEN tool_name='search_brand' THEN 1 ELSE 0 END) AS searches_count,
                       SUM(CASE WHEN tool_name='browse_page' THEN 1 ELSE 0 END) AS pages_browsed,
                       COALESCE(SUM(token_estimate), 0) AS total_output_tokens_estimate
                FROM tool_results WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()

            data = dict(session) if session else {"session_id": session_id, "turn_count": 0, "duration_seconds": 0.0}
            data.update(dict(counts) if counts else {})
            data["total_input_tokens_estimate"] = data.get("total_output_tokens_estimate", 0)
            return data

    def close_session(self, session_id: str) -> dict[str, Any]:
        telemetry = self.telemetry(session_id)
        with self._connect() as conn:
            conn.execute(
                "UPDATE worker_sessions SET ended_at = datetime('now'), status = 'completed' WHERE session_id = ?",
                (session_id,),
            )
            conn.execute(
                """
                INSERT INTO session_telemetry(
                    session_id, tool_calls_count, searches_count, pages_browsed,
                    total_input_tokens_estimate, total_output_tokens_estimate, duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    telemetry.get("tool_calls_count", 0),
                    telemetry.get("searches_count", 0),
                    telemetry.get("pages_browsed", 0),
                    telemetry.get("total_input_tokens_estimate", 0),
                    telemetry.get("total_output_tokens_estimate", 0),
                    telemetry.get("duration_seconds", 0.0),
                ),
            )
        return telemetry
