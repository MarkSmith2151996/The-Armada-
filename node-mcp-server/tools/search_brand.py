from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from config import Settings
from local_store import ContextStore


logger = logging.getLogger(__name__)


class SearchKeyUnavailable(RuntimeError):
    """A provider rejected a key because it is unusable or out of credits."""


class SearchKeyPool:
    def __init__(self, config_path: Path, fallback_key: str, fallback_url: str) -> None:
        self.keys = self._load_keys(config_path, fallback_key, fallback_url)
        self.current_key_index = 0
        self.dead_keys: set[int] = set()

    @staticmethod
    def _load_keys(config_path: Path, fallback_key: str, fallback_url: str) -> list[dict[str, str]]:
        if config_path.exists():
            try:
                payload = json.loads(config_path.read_text(encoding="utf-8"))
                keys = [
                    {"provider": item["provider"].lower(), "key": item["key"], "endpoint": item["endpoint"]}
                    for item in payload.get("keys", [])
                    if all(isinstance(item.get(field), str) and item[field] for field in ("provider", "key", "endpoint"))
                ]
                if keys:
                    return keys
                logger.warning("Search key configuration %s contains no usable keys", config_path)
            except (OSError, ValueError, TypeError) as exc:
                logger.warning("Unable to load search key configuration %s: %s", config_path, exc)
        if fallback_key:
            return [{"provider": "serper", "key": fallback_key, "endpoint": fallback_url}]
        return []

    def current_key(self) -> tuple[int, dict[str, str]]:
        for _ in range(len(self.keys)):
            if self.current_key_index not in self.dead_keys:
                return self.current_key_index, self.keys[self.current_key_index]
            self.current_key_index = (self.current_key_index + 1) % len(self.keys)
        raise SearchKeyUnavailable("All configured search API keys are unavailable")

    def retire_current_key(self) -> None:
        index, key = self.current_key()
        logger.warning("Key %d (%s) exhausted, rotating to next key", index, key["provider"])
        self.dead_keys.add(index)
        if len(self.dead_keys) < len(self.keys):
            self.current_key_index = (index + 1) % len(self.keys)


_key_pool: SearchKeyPool | None = None


def _get_key_pool(settings: Settings) -> SearchKeyPool:
    global _key_pool
    if _key_pool is None:
        config_path = Path(__file__).resolve().parent.parent / "search_keys.json"
        _key_pool = SearchKeyPool(config_path, settings.search_api_key, settings.search_api_url)
    return _key_pool


def _key_is_unavailable(response: requests.Response, payload: Any | None = None) -> bool:
    if response.status_code in (401, 402, 403):
        return True
    if not isinstance(payload, dict):
        try:
            payload = response.json()
        except ValueError:
            payload = {}
    message = " ".join(str(payload.get(field, "")) for field in ("message", "error", "code")).lower()
    return any(marker in message for marker in ("insufficient credit", "credit exhausted", "out of credit", "billing", "invalid api key", "expired api key"))


def _search_with_key(settings: Settings, key_config: dict[str, str], query: str, num_results: int) -> tuple[list[dict[str, str]], dict[str, Any]]:
    provider = key_config["provider"]
    headers = {"X-API-KEY": key_config["key"]}
    if provider == "serper":
        response = requests.post(key_config["endpoint"], headers={**headers, "Content-Type": "application/json"}, json={"q": query, "num": num_results}, timeout=settings.request_timeout_seconds)
    elif provider == "searlo":
        response = requests.get(key_config["endpoint"], headers=headers, params={"q": query, "limit": num_results}, timeout=settings.request_timeout_seconds)
    else:
        raise RuntimeError(f"Unsupported search provider: {provider}")

    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if _key_is_unavailable(response, payload):
        raise SearchKeyUnavailable(f"{provider} rejected the API key")
    response.raise_for_status()
    if isinstance(payload, dict) and payload.get("success") is False:
        raise RuntimeError(payload.get("message") or payload.get("error") or f"{provider} search failed")

    items = payload.get("organic", []) if provider == "serper" else payload.get("items", payload.get("organic", []))
    return [{"title": item.get("title", ""), "url": item.get("link", ""), "snippet": item.get("snippet", "")} for item in items], payload


def serper_search(settings: Settings, query: str, num_results: int = 10) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Search with the configured key pool, retiring only rejected or exhausted keys."""
    pool = _get_key_pool(settings)
    while True:
        index, key_config = pool.current_key()
        logger.info("Using search key %d (%s) for %r", index, key_config["provider"], query)
        try:
            return _search_with_key(settings, key_config, query, num_results)
        except SearchKeyUnavailable:
            pool.retire_current_key()


def searxng_search(settings: Settings, query: str) -> tuple[list[dict[str, str]], dict[str, Any]]:
    response = requests.get(settings.searxng_search_url, params={"q": query, "format": "json"}, timeout=settings.request_timeout_seconds)
    response.raise_for_status()
    payload = response.json()
    results = [{"title": item.get("title", ""), "url": item.get("url", ""), "snippet": item.get("content") or item.get("snippet") or ""} for item in payload.get("results", [])]
    return results, payload


def handle_search_brand(*, settings: Settings, store: ContextStore, brand_name: str, query: str, session_id: str = "", ai_id: str = "") -> dict[str, Any]:
    session_id = store.ensure_session(session_id, brand_name, ai_id)
    turn = store.increment_turn(session_id, brand_name, ai_id)
    search_query = query.strip() or brand_name.strip()
    try:
        backend = "Serper"
        try:
            results, payload = serper_search(settings, search_query)
        except Exception as serper_error:
            backend = "SearXNG"
            logger.warning("Search API failed for %r; falling back to SearXNG: %s", search_query, serper_error)
            results, payload = searxng_search(settings, search_query)
        else:
            logger.info("Search API served %r", search_query)
        compact = [{"title": item.get("title", "")[:180], "url": item.get("url", ""), "snippet": item.get("snippet", "")[:500]} for item in results[:3]]
        summary = f"{backend}: {len(results)} search results for {search_query}; returned top {len(compact)}."
        result_id = store.add_tool_result(session_id=session_id, turn=turn, tool_name="search_brand", query=search_query, result_summary=summary, full_result={"backend": backend, "payload": payload})
        return {"ok": True, "session_id": session_id, "turn": turn, "stored_result_id": result_id, "query": search_query, "summary": summary, "top_results": compact}
    except Exception as exc:
        summary = f"search_brand failed for {search_query}: {exc}"
        result_id = store.add_tool_result(session_id=session_id, turn=turn, tool_name="search_brand", query=search_query, result_summary=summary, full_result={"error": str(exc), "search_api_url": settings.search_api_url, "search_url": settings.searxng_search_url})
        return {"ok": False, "session_id": session_id, "turn": turn, "stored_result_id": result_id, "query": search_query, "error": str(exc), "hint": "Check SEARCH_API_URL/SEARCH_API_KEY and SEARXNG_SEARCH_URL."}
