from __future__ import annotations

import json
from typing import Any

from config import Settings


WORKER_VERDICTS_SQL = """
CREATE TABLE IF NOT EXISTS fba.worker_verdicts (
    id SERIAL PRIMARY KEY,
    brand_name TEXT NOT NULL,
    brand_slug TEXT NOT NULL,
    verdict TEXT NOT NULL,
    confidence TEXT,
    wholesale_url TEXT,
    restrictions TEXT,
    distributor TEXT,
    contact_method TEXT,
    notes TEXT,
    ai_id TEXT,
    node TEXT,
    session_duration_seconds REAL,
    turn_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_worker_verdicts_brand ON fba.worker_verdicts(brand_slug);
CREATE INDEX IF NOT EXISTS idx_worker_verdicts_verdict ON fba.worker_verdicts(verdict);
"""
def _connect(settings: Settings):
    if not settings.postgres_dsn:
        return None, {"ok": False, "skipped": True, "reason": "FBA_POSTGRES_DSN/FBA_DATABASE_URL/POSTGRES_DSN/DATABASE_URL is unset"}
    try:
        import psycopg2

        return psycopg2.connect(settings.postgres_dsn), None
    except Exception as exc:
        return None, {"ok": False, "error": str(exc), "hint": "Install psycopg2-binary and set FBA_POSTGRES_DSN."}


def write_verdict(settings: Settings, verdict: dict[str, Any], telemetry: dict[str, Any]) -> dict[str, Any]:
    conn, error = _connect(settings)
    if error:
        return error

    assert conn is not None
    try:
        from psycopg2.extras import Json

        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute("SELECT to_regnamespace(%s)", ("fba",))
            if not cur.fetchone()[0]:
                return {"ok": False, "error": "Postgres schema fba is missing"}

            worker_verdict_id = None
            worker_verdict_result: dict[str, Any] = {"ok": False, "skipped": True, "reason": "fba.worker_verdicts is absent"}
            cur.execute("SELECT to_regclass(%s)", ("fba.worker_verdicts",))
            worker_verdicts_exists = bool(cur.fetchone()[0])
            if not worker_verdicts_exists:
                cur.execute("SELECT has_schema_privilege(current_user, %s, %s)", ("fba", "CREATE"))
                if cur.fetchone()[0]:
                    cur.execute(WORKER_VERDICTS_SQL)
                    worker_verdicts_exists = True

            if worker_verdicts_exists:
                cur.execute(
                    """
                    INSERT INTO fba.worker_verdicts(
                        brand_name, brand_slug, verdict, confidence, wholesale_url, restrictions,
                        distributor, contact_method, notes, ai_id, node,
                        session_duration_seconds, turn_count
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        verdict["brand_name"],
                        verdict["brand_slug"],
                        verdict["verdict"],
                        verdict.get("confidence"),
                        verdict.get("wholesale_url"),
                        verdict.get("restrictions"),
                        verdict.get("distributor"),
                        verdict.get("contact_method"),
                        verdict.get("notes"),
                        verdict.get("ai_id"),
                        settings.node_name,
                        telemetry.get("duration_seconds"),
                        telemetry.get("turn_count"),
                    ),
                )
                worker_verdict_id = cur.fetchone()[0]
                worker_verdict_result = {"ok": True, "id": worker_verdict_id}

            cur.execute("SELECT to_regclass(%s)", ("fba.artifact",))
            artifact_table = cur.fetchone()[0]
            artifact_result: dict[str, Any]
            if artifact_table:
                analysis = json.dumps(verdict, ensure_ascii=True, sort_keys=True)
                cur.execute(
                    f"""
                    INSERT INTO {artifact_table}(
                        category, subject, title, summary, analysis, status,
                        source_task, metadata, token_count, content_hash, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now())
                    ON CONFLICT (subject) DO UPDATE SET
                        title = excluded.title,
                        summary = excluded.summary,
                        analysis = excluded.analysis,
                        status = excluded.status,
                        source_task = excluded.source_task,
                        metadata = COALESCE({artifact_table}.metadata, '{{}}'::jsonb) || excluded.metadata,
                        token_count = excluded.token_count,
                        content_hash = excluded.content_hash,
                        updated_at = now()
                    RETURNING id
                    """,
                    (
                        "outreach_intel",
                        f"outreach:{verdict['brand_slug']}",
                        f"{verdict['brand_name']} - Outreach Intelligence",
                        (verdict.get('notes') or "")[:1000],
                        analysis,
                        verdict["verdict"],
                        verdict.get("ai_id"),
                        Json(verdict),
                        telemetry.get("total_output_tokens_estimate"),
                        None,
                    ),
                )
                artifact_result = {"ok": True, "table": artifact_table, "id": cur.fetchone()[0]}
            else:
                artifact_result = {"ok": False, "skipped": True, "reason": "fba.artifact was not present"}

        conn.commit()
        return {
            "ok": bool(worker_verdict_result.get("ok") or artifact_result.get("ok")),
            "worker_verdict_id": worker_verdict_id,
            "worker_verdict": worker_verdict_result,
            "artifact": artifact_result,
        }
    except Exception as exc:
        conn.rollback()
        return {"ok": False, "error": str(exc)}
    finally:
        conn.close()
