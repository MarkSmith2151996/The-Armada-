from __future__ import annotations

from typing import Any

from local_store import ContextStore


def handle_get_context(
    *,
    store: ContextStore,
    query: str,
    session_id: str,
    limit: int = 3,
) -> dict[str, Any]:
    matches = store.search_context(session_id=session_id, query=query, limit=max(1, min(limit, 10)))
    return {
        "ok": True,
        "session_id": session_id,
        "query": query,
        "matches": matches,
        "count": len(matches),
    }
