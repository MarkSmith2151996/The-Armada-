#!/usr/bin/env python3
"""Search ImportYeti and export importer rows to CSV."""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import sys
import time
from collections import defaultdict
from typing import Any

import requests


SEARCH_URL = "https://www.importyeti.com/api/search"
COMPANY_URL = "https://www.importyeti.com/{slug}"
DETAIL_API_URL = "https://data.importyeti.com/v1.0/{slug}"
JINA_PREFIX = "https://r.jina.ai/http://"
DEFAULT_SLEEP = 2.5
BACKOFFS = (5, 10, 20)
DIRECT_SEARCH_BLOCKED = False
DIRECT_COMPANY_BLOCKED = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", help="Single search query")
    parser.add_argument("--queries", nargs="+", help="Multiple search queries")
    parser.add_argument("--min-shipments", type=int, default=50)
    parser.add_argument("--country-code", default="US")
    parser.add_argument("--type-filter", default="company")
    parser.add_argument("--max-results", type=int, default=100)
    parser.add_argument("--output", required=True)
    parser.add_argument("--cookie", default=os.getenv("IMPORTYETI_COOKIE", ""))
    parser.add_argument("--api-key", default=os.getenv("IMPORTYETI_API_KEY", ""))
    parser.add_argument("--sleep-seconds", type=float, default=DEFAULT_SLEEP)
    args = parser.parse_args()
    queries = []
    if args.query:
        queries.append(args.query)
    if args.queries:
        queries.extend(args.queries)
    if not queries:
        parser.error("Provide --query or --queries")
    args.queries = queries
    return args


def make_session(cookie: str = "", api_key: str = "") -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    if cookie:
        session.headers["Cookie"] = cookie
    if api_key:
        session.headers["Authorization"] = f"Bearer {api_key}"
    return session


def sleep_log(seconds: float, reason: str) -> None:
    print(f"sleeping {seconds:.1f}s: {reason}", file=sys.stderr)
    time.sleep(seconds)


def is_blocked(response: requests.Response) -> bool:
    text = response.text[:500].lower()
    return response.status_code in {403, 429} or "just a moment" in text or "cloudflare" in text


def get_with_backoff(session: requests.Session, url: str, *, params: dict[str, Any] | None = None) -> requests.Response:
    last_response: requests.Response | None = None
    for attempt in range(len(BACKOFFS) + 1):
        response = session.get(url, params=params, timeout=60)
        last_response = response
        if response.ok and not is_blocked(response):
            return response
        if attempt >= len(BACKOFFS):
            break
        if response.status_code >= 500 or is_blocked(response):
            sleep_log(BACKOFFS[attempt], f"retry {attempt + 1} for {response.status_code} {url}")
            continue
        response.raise_for_status()
    if last_response is None:
        raise RuntimeError(f"No response returned for {url}")
    last_response.raise_for_status()
    raise RuntimeError(f"Blocked while requesting {url}")


def parse_maybe_wrapped_json(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in response")
    return json.loads(text[start : end + 1])


def fetch_search_page(session: requests.Session, query: str, page: int) -> dict[str, Any]:
    global DIRECT_SEARCH_BLOCKED
    params = {"q": query, "page": page}
    if not DIRECT_SEARCH_BLOCKED:
        try:
            response = get_with_backoff(session, SEARCH_URL, params=params)
            return response.json()
        except Exception as exc:
            DIRECT_SEARCH_BLOCKED = True
            print(f"direct search blocked for '{query}' page {page}: {exc}", file=sys.stderr)
    mirror = f"{JINA_PREFIX}{SEARCH_URL}?q={requests.utils.quote(query)}&page={page}"
    response = get_with_backoff(session, mirror)
    return parse_maybe_wrapped_json(response.text)


def extract_json_array(text: str, key: str) -> list[dict[str, Any]]:
    normalized = html.unescape(text).replace('\\"', '"')
    marker = f'"{key}":['
    start = normalized.find(marker)
    if start == -1:
        return []
    idx = start + len(marker) - 1
    depth = 0
    for pos in range(idx, len(normalized)):
        char = normalized[pos]
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                raw = normalized[idx : pos + 1]
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    return []
                return [item for item in data if isinstance(item, dict)]
    return []


def extract_trademark_count(text: str) -> int:
    match = re.search(r"Trademarks\s+(\d+)", text, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def fetch_trademarks(session: requests.Session, slug: str) -> tuple[list[str], str]:
    global DIRECT_COMPANY_BLOCKED
    if "Authorization" in session.headers:
        try:
            response = get_with_backoff(session, DETAIL_API_URL.format(slug=slug))
            data = parse_maybe_wrapped_json(response.text).get("data", {})
            names = [item.get("name", "").strip() for item in data.get("trademarks", []) if item.get("name")]
            return dedupe(names), "detail_api"
        except Exception:
            pass

    if not DIRECT_COMPANY_BLOCKED:
        try:
            response = get_with_backoff(session, COMPANY_URL.format(slug=slug))
            names = [item.get("name", "").strip() for item in extract_json_array(response.text, "trademarks") if item.get("name")]
            return dedupe(names), "company_html"
        except Exception:
            DIRECT_COMPANY_BLOCKED = True

    try:
        mirror = f"{JINA_PREFIX}{COMPANY_URL.format(slug=slug)}"
        response = get_with_backoff(session, mirror)
        count = extract_trademark_count(response.text)
        if count:
            print(f"trademark names unavailable for {slug}; page reports count={count}", file=sys.stderr)
        return [], "jina_company_text"
    except Exception:
        return [], "unavailable"


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        lowered = cleaned.lower()
        if cleaned and lowered not in seen:
            seen.add(lowered)
            result.append(cleaned)
    return result


def search_query(session: requests.Session, query: str, args: argparse.Namespace) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    page = 1
    while len(rows) < args.max_results:
        payload = fetch_search_page(session, query, page)
        results = payload.get("searchResults", [])
        if not results:
            break
        for result in results:
            if result.get("type") != args.type_filter:
                continue
            if args.country_code and result.get("countryCode") != args.country_code:
                continue
            if int(result.get("totalShipments") or 0) < args.min_shipments:
                continue
            slug = result.get("url", "")
            trademarks, source = fetch_trademarks(session, slug) if slug else ([], "none")
            rows.append(
                {
                    "company_name": result.get("title", ""),
                    "trademarks": "|".join(trademarks),
                    "total_shipments": result.get("totalShipments", ""),
                    "country": result.get("countryCode", ""),
                    "address": result.get("address", ""),
                    "last_shipment_date": result.get("mostRecentShipment", ""),
                    "importyeti_url": f"https://www.importyeti.com/{slug}",
                    "search_query": query,
                    "detail_source": source,
                }
            )
            if len(rows) >= args.max_results:
                break
            sleep_log(args.sleep_seconds, f"respect rate limit after {slug}")
        total_pages = int(payload.get("totalPages") or page)
        if len(rows) >= args.max_results or page >= total_pages:
            break
        page += 1
        sleep_log(args.sleep_seconds, f"next page for '{query}'")
    return rows


def write_csv(path: str, rows: list[dict[str, Any]]) -> None:
    fields = [
        "company_name",
        "trademarks",
        "total_shipments",
        "country",
        "address",
        "last_shipment_date",
        "importyeti_url",
        "search_query",
    ]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def print_summary(rows: list[dict[str, Any]]) -> None:
    per_query: dict[str, int] = defaultdict(int)
    trademarks: set[str] = set()
    detail_sources: dict[str, int] = defaultdict(int)
    for row in rows:
        per_query[row["search_query"]] += 1
        detail_sources[row.get("detail_source", "unknown")] += 1
        for mark in row["trademarks"].split("|"):
            if mark:
                trademarks.add(mark)
    print("summary", json.dumps({
        "rows": len(rows),
        "per_query": per_query,
        "unique_trademarks": len(trademarks),
        "detail_sources": detail_sources,
    }, default=dict))


def main() -> int:
    args = parse_args()
    session = make_session(cookie=args.cookie, api_key=args.api_key)
    all_rows: list[dict[str, Any]] = []
    for query in args.queries:
        print(f"querying '{query}'", file=sys.stderr)
        all_rows.extend(search_query(session, query, args))
    write_csv(args.output, all_rows)
    print_summary(all_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
