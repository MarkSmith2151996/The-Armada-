#!/usr/bin/env python3
from __future__ import annotations

import time

from config import get_settings
from local_store import ContextStore
from tools.edge_store import SqldStore
from tools.get_context import handle_get_context
from tools.record_verdict import handle_record_verdict
from tools.search_brand import handle_search_brand


def main() -> int:
    settings = get_settings()
    session_id = f"AI-SMOKE-{int(time.time())}"
    print("settings", {"db_path": str(settings.db_path), "node": settings.node_name})

    search = handle_search_brand(
        settings=settings,
        store=ContextStore(settings),
        brand_name="Westclox",
        query="Westclox wholesale portal",
        session_id=session_id,
        ai_id=session_id,
    )
    print("search_brand", {"ok": search.get("ok"), "stored_result_id": search.get("stored_result_id"), "error": search.get("error")})

    context = handle_get_context(store=ContextStore(settings), query="wholesale portal", session_id=session_id, limit=3)
    print("get_context", {"ok": context.get("ok"), "count": context.get("count")})

    verdict = handle_record_verdict(
        settings=settings,
        brand_name="Westclox Smoke Test",
        brand_slug="westclox_smoke_test",
        verdict="INCONCLUSIVE",
        confidence="LOW",
        wholesale_url="",
        restrictions="smoke test only",
        distributor="",
        contact_method="none",
        notes="Local integration smoke test; external writes disabled.",
        ai_id=session_id,
        session_id=session_id,
    )
    SqldStore(settings).execute("DELETE FROM verdicts WHERE instruction_id = ?", [session_id])
    print("record_verdict", {"ok": verdict.get("ok"), "queued_for_sync": verdict.get("queued_for_sync")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
