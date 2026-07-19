from __future__ import annotations

import logging
import re
from typing import Any

from config import Settings
from tools.edge_store import SqldStore


VALID_VERDICTS = {
    "ACCESSIBLE",
    "MAYBE",
    "CLOSED",
    "PRIVATE_LABEL",
    "GATED",
    "BLOCKED_FOR_AMAZON",
    "INCONCLUSIVE",
}
VALID_CONFIDENCE = {"HIGH", "MEDIUM", "LOW", ""}
AI_ID_PATTERN = re.compile(r"AI-\d{5}\Z")
logger = logging.getLogger(__name__)


def _slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "unknown"


def handle_record_verdict(
    *,
    settings: Settings,
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
    verdict = verdict.strip().upper()
    confidence = confidence.strip().upper()
    brand_slug = _slug(brand_slug or brand_name)
    if verdict not in VALID_VERDICTS:
        return {"ok": False, "error": f"Invalid verdict {verdict!r}", "valid_verdicts": sorted(VALID_VERDICTS)}
    if confidence not in VALID_CONFIDENCE:
        return {"ok": False, "error": f"Invalid confidence {confidence!r}", "valid_confidence": sorted(v for v in VALID_CONFIDENCE if v)}
    if not AI_ID_PATTERN.fullmatch(ai_id):
        return {"ok": False, "error": "Invalid ai_id: must be in format AI-XXXXX"}

    verdict_payload = {
        "brand_name": brand_name,
        "brand_slug": brand_slug,
        "verdict": verdict,
        "confidence": confidence,
        "wholesale_url": wholesale_url,
        "restrictions": restrictions,
        "distributor": distributor,
        "contact_method": contact_method,
        "notes": notes,
        "ai_id": ai_id,
        "session_id": session_id,
    }
    try:
        edge_store.insert_verdict(verdict_payload)
    except Exception as exc:
        return {"ok": False, "error": f"Local sqld write failed: {exc}"}

    return {
        "ok": True,
        "queued_for_sync": True,
        "verdict": verdict_payload,
    }
