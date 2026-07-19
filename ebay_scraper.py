"""One-shot eBay search-lake scraper using Armada's leased Chrome CDP pool."""

from __future__ import annotations

import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin

from bs4 import BeautifulSoup
from playwright.async_api import Browser, BrowserContext, Page, Playwright, TimeoutError as PlaywrightTimeoutError, async_playwright


REPO_ROOT = Path(__file__).resolve().parent
NODE_MCP_DIR = REPO_ROOT / "node-mcp-server"
if str(NODE_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(NODE_MCP_DIR))

from cdp_pool import ensure_initialized, pool  # noqa: E402


EBAY_HOME_URL = "https://www.ebay.com"
SEARCH_BASE_URL = "https://www.ebay.com/sch/i.html"
QUERIES = (
    # === Original broad motherboard ===
    "motherboard for parts",
    "motherboard bent pin",
    "motherboard damaged",
    "motherboard as-is",
    "mobo for parts",
    "mainboard for parts",
    # === AM5 Motherboard/Socket ===
    "AM5 motherboard for parts",
    "AM5 motherboard not working",
    "AM5 bent cpu",
    "AM5 pins",
    "AM5 motherboard broken",
    "AM5 motherboard parts only",
    # === AM5 High-end chipsets ===
    "X870E bent",
    "X870 bent",
    "X670E bent",
    "X670 bent",
    # === AM5 Mid-range chipsets ===
    "B650E bent",
    "B650 bent",
    # === AM4 CPU broad ===
    "AM4 CPU bent pins",
    "AM4 CPU for parts",
    "AM4 CPU not working",
    "AM4 Ryzen bent pins",
    "AM4 Ryzen for parts",
    # === Ryzen CPU general ===
    "Ryzen bent pins",
    "Ryzen CPU for parts",
    "Ryzen processor bent",
    # === Ryzen tier-specific ===
    "Ryzen 5 bent pins",
    "Ryzen 7 bent pins",
    "Ryzen 9 bent pins",
    # === High-value AMD models ===
    "5800X3D bent",
    "5800X3D for parts",
    "5900X bent",
    "5950X bent",
    "5600X bent",
    "5700X3D bent",
    # === AMD pin-specific ===
    "Ryzen CPU pins broken",
    "Ryzen CPU pins damaged",
    "AM4 processor pins",
    # === Intel LGA (pins on motherboard socket) ===
    "LGA 1700 bent pin",
    "LGA 1700 motherboard for parts",
    "LGA 1700 bent socket",
    "Z790 bent pin",
    "Z790 motherboard for parts",
    "Z690 bent pin",
    "Z690 motherboard for parts",
    "B760 motherboard for parts",
    "LGA 1200 bent pin",
    "LGA 1200 motherboard for parts",
)
PAGES_PER_QUERY = 5
ITEMS_PER_PAGE = 240
NAVIGATION_TIMEOUT_MS = 45_000
POST_LOAD_WAIT_MS = 2_500
PAGE_PACE_MS = 6_000
RESULTS_PATH = REPO_ROOT / "ebay_scrape_results_v2.json"
SEARCH_DEBUG_PATH = REPO_ROOT / "debug_search_page.html"
EMPTY_DEBUG_PATH = REPO_ROOT / "debug_empty_page.html"

PRICE_PATTERN = re.compile(r"(?:US\s*)?\$\s*[\d,.]+(?:\s+to\s+(?:US\s*)?\$\s*[\d,.]+)?", re.IGNORECASE)
ITEM_ID_PATTERN = re.compile(r"/itm/(?:[^/?#]+/)?(\d{9,})")
BOT_DETECTION_MARKERS = (
    "captcha",
    "security challenge",
    "verify yourself",
    "pardon the interruption",
    "robot check",
    "access denied",
    "automated access",
    "unusual traffic",
)


def _clean_text(value: str | None) -> str | None:
    if not value:
        return None
    text = re.sub(r"\s+", " ", value).strip()
    return text or None


def _node_text(node: Any) -> str | None:
    if node is None:
        return None
    return _clean_text(node.get_text(" ", strip=True))


def _first_text(root: Any, selectors: tuple[str, ...]) -> str | None:
    for selector in selectors:
        value = _node_text(root.select_one(selector))
        if value:
            return value
    return None


def _first_attribute(root: Any, selectors: tuple[str, ...], attributes: tuple[str, ...]) -> str | None:
    for selector in selectors:
        node = root.select_one(selector)
        if node is None:
            continue
        for attribute in attributes:
            value = node.get(attribute)
            if value:
                return str(value)
    return None


def _search_url(query: str, page_number: int) -> str:
    parameters = {
        "_nkw": query,
        "LH_ItemCondition": "7000",
        "_sop": "10",
        "_ipg": str(ITEMS_PER_PAGE),
        "_pgn": str(page_number),
    }
    return f"{SEARCH_BASE_URL}?{urlencode(parameters)}"


def _item_id(item_url: str | None) -> str | None:
    if not item_url:
        return None
    match = ITEM_ID_PATTERN.search(item_url)
    return match.group(1) if match else None


def _listing_type(card_text: str) -> str:
    normalized = card_text.lower()
    if "best offer" in normalized:
        return "Best Offer"
    if "auction" in normalized or re.search(r"\b\d[\d,]*\s+bids?\b", normalized):
        return "Auction"
    return "Buy It Now"


def _extract_price(card: Any) -> str | None:
    price_source = _first_text(
        card,
        (
            ".su-card-container__attributes",
            ".s-card__price",
            "[class*='price']",
        ),
    )
    match = PRICE_PATTERN.search(price_source or "")
    return _clean_text(match.group(0)) if match else None


def _extract_shipping(card: Any, card_text: str) -> str | None:
    explicit = _first_text(card, ("[class*='shipping']", "[class*='delivery']"))
    if explicit:
        return explicit
    match = re.search(
        r"\bFree\s+(?:shipping|delivery)\b|(?:\+\s*)?\$\s*[\d,.]+\s+(?:shipping|delivery)\b",
        card_text,
        re.IGNORECASE,
    )
    return _clean_text(match.group(0)) if match else None


def _extract_location(card: Any) -> str | None:
    explicit = _first_text(card, ("[class*='location']", "[data-testid*='location']"))
    if explicit:
        return explicit
    for line in card.get_text("\n", strip=True).splitlines():
        match = re.search(r"\b(?:located in|item location)\s*:\s*(.+)$", line, re.IGNORECASE)
        if match:
            return _clean_text(match.group(1))
    return None


def _extract_condition(card: Any, card_text: str) -> str | None:
    explicit = _first_text(card, ("[class*='condition']", ".s-card__subtitle"))
    if explicit:
        return explicit
    match = re.search(
        r"\b(?:for parts or not working|seller refurbished|pre-owned|open box|used|new)\b",
        card_text,
        re.IGNORECASE,
    )
    return _clean_text(match.group(0)) if match else None


def _extract_seller(card: Any) -> str | None:
    seller = _first_text(card, ("[class*='seller']", "[data-testid*='seller']"))
    if seller:
        return re.sub(r"^seller:\s*", "", seller, flags=re.IGNORECASE)
    for line in card.get_text("\n", strip=True).splitlines():
        match = re.search(r"^seller:\s*(.+)$", line, re.IGNORECASE)
        if match:
            return _clean_text(match.group(1))
    return None


def _listing_cards(soup: BeautifulSoup) -> list[Any]:
    container = soup.select_one("ul.srp-results")
    if container is None:
        return []
    return [
        child
        for child in container.find_all("li", recursive=False)
        if "s-card" in (child.get("class") or [])
    ]


def _parse_search_page(html: str, query: str, page_number: int) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    listings: list[dict[str, Any]] = []
    for card in _listing_cards(soup):
        raw_item_url = _first_attribute(card, ("a.s-card__link[href]",), ("href",))
        item_url = urljoin(SEARCH_BASE_URL, raw_item_url) if raw_item_url else None
        title = _first_text(
            card,
            (
                "span.su-styled-text.primary.default",
                "span.su-styled-text.primary",
                ".s-card__title",
            ),
        )
        if not item_url and not title:
            continue
        card_text = _clean_text(card.get_text(" ", strip=True)) or ""
        thumbnail_url = _first_attribute(
            card,
            (".s-card__image img", "img"),
            ("data-src", "data-original", "src"),
        )
        listings.append(
            {
                "item_id": _item_id(item_url),
                "title": title,
                "price": _extract_price(card),
                "listing_type": _listing_type(card_text),
                "shipping": _extract_shipping(card, card_text),
                "seller_name": _extract_seller(card),
                "thumbnail_url": urljoin(SEARCH_BASE_URL, thumbnail_url) if thumbnail_url else None,
                "item_url": item_url,
                "condition_text": _extract_condition(card, card_text),
                "location": _extract_location(card),
                "search_query": query,
                "page_number": page_number,
            }
        )
    return listings


def _is_bot_detection_page(html: str) -> bool:
    lowered = html.lower()
    return any(marker in lowered for marker in BOT_DETECTION_MARKERS)


def _save_results(results: dict[str, Any]) -> None:
    results["unique_listings"] = len(results["listings"])
    temporary_path = RESULTS_PATH.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary_path.replace(RESULTS_PATH)


async def _navigate(page: Page, url: str) -> int | None:
    response = await page.goto(url, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)
    await page.wait_for_timeout(POST_LOAD_WAIT_MS)
    return response.status if response is not None else None


def _print_progress(query_index: int, page_number: int, results: dict[str, Any]) -> None:
    print(
        f"[query {query_index}/{len(QUERIES)}, page {page_number}/{PAGES_PER_QUERY}] "
        f"{results['unique_listings']} unique listings so far"
    )


def _print_summary(results: dict[str, Any]) -> None:
    print("\nScrape summary")
    print(f"  Pages scraped: {results['total_pages_scraped']}")
    print(f"  Listings seen: {results['total_listings_seen']}")
    print(f"  Unique listings: {results['unique_listings']}")
    print(f"  Duplicates skipped: {results['duplicates_skipped']}")
    print(f"  Results: {RESULTS_PATH}")


async def main() -> None:
    results: dict[str, Any] = {
        "scrape_time": datetime.now(timezone.utc).isoformat(),
        "queries": list(QUERIES),
        "pages_per_query": PAGES_PER_QUERY,
        "items_per_page": ITEMS_PER_PAGE,
        "total_pages_scraped": 0,
        "total_listings_seen": 0,
        "unique_listings": 0,
        "duplicates_skipped": 0,
        "listings": [],
    }
    seen_item_ids: set[str] = set()
    playwright: Playwright | None = None
    browser: Browser | None = None
    context: BrowserContext | None = None
    page: Page | None = None
    created_context = False
    acquired_port: int | None = None
    debug_search_saved = False

    _save_results(results)
    try:
        ensure_initialized()
        acquired = pool.acquire("ebay-scraper")
        if acquired.get("status") != "acquired":
            raise RuntimeError(str(acquired.get("error") or "No CDP pool slot is available"))
        acquired_port = int(acquired["port"])
        print(f"Acquired Chrome CDP port {acquired_port}")

        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(f"http://localhost:{acquired_port}")
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = await browser.new_context()
            created_context = True
        page = await context.new_page()
        page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)

        try:
            await _navigate(page, EBAY_HOME_URL)
            await page.wait_for_timeout(2_000)
            print("eBay homepage loaded; search session established")
        except Exception as exc:
            print(f"Homepage navigation failed; continuing with search pages: {exc}")

        for query_index, query in enumerate(QUERIES, start=1):
            for page_number in range(1, PAGES_PER_QUERY + 1):
                try:
                    response_status = await _navigate(page, _search_url(query, page_number))
                    html = await page.content()
                except PlaywrightTimeoutError as exc:
                    print(f"[query {query_index}/{len(QUERIES)}, page {page_number}/{PAGES_PER_QUERY}] timed out: {exc}")
                    _save_results(results)
                    if page_number < PAGES_PER_QUERY:
                        await page.wait_for_timeout(PAGE_PACE_MS)
                    continue
                except Exception as exc:
                    print(f"[query {query_index}/{len(QUERIES)}, page {page_number}/{PAGES_PER_QUERY}] failed: {exc}")
                    _save_results(results)
                    if page_number < PAGES_PER_QUERY:
                        await page.wait_for_timeout(PAGE_PACE_MS)
                    continue

                results["total_pages_scraped"] += 1
                if response_status is not None and response_status >= 400:
                    print(
                        f"[query {query_index}/{len(QUERIES)}, page {page_number}/{PAGES_PER_QUERY}] "
                        f"navigation returned HTTP {response_status}; attempting to parse the response."
                    )
                try:
                    page_listings = _parse_search_page(html, query, page_number)
                except Exception as exc:
                    print(f"[query {query_index}/{len(QUERIES)}, page {page_number}/{PAGES_PER_QUERY}] parse failed: {exc}")
                    _save_results(results)
                    if page_number < PAGES_PER_QUERY:
                        await page.wait_for_timeout(PAGE_PACE_MS)
                    continue
                if not page_listings:
                    EMPTY_DEBUG_PATH.write_text(html, encoding="utf-8")
                    bot_message = " eBay CAPTCHA or bot-detection page detected." if _is_bot_detection_page(html) else ""
                    print(
                        f"[query {query_index}/{len(QUERIES)}, page {page_number}/{PAGES_PER_QUERY}] "
                        f"0 listing cards; stopping this query.{bot_message}"
                    )
                    _save_results(results)
                    if query_index < len(QUERIES):
                        await page.wait_for_timeout(PAGE_PACE_MS)
                    break

                if not debug_search_saved:
                    SEARCH_DEBUG_PATH.write_text(html, encoding="utf-8")
                    debug_search_saved = True

                for listing in page_listings:
                    results["total_listings_seen"] += 1
                    item_id = listing["item_id"]
                    if item_id and item_id in seen_item_ids:
                        results["duplicates_skipped"] += 1
                        continue
                    if item_id:
                        seen_item_ids.add(item_id)
                    results["listings"].append(listing)

                _save_results(results)
                _print_progress(query_index, page_number, results)
                if page_number < PAGES_PER_QUERY:
                    await page.wait_for_timeout(PAGE_PACE_MS)
    except KeyboardInterrupt:
        print("Interrupted; preserving partial JSON output.")
    except Exception as exc:
        print(f"Scraper setup failed: {exc}")
    finally:
        _save_results(results)
        if page is not None:
            try:
                await page.close()
            except Exception:
                pass
        if created_context and context is not None:
            try:
                await context.close()
            except Exception:
                pass
        if browser is not None:
            try:
                await browser._impl_obj._connection.stop_async()
            except Exception:
                pass
        elif playwright is not None:
            try:
                await playwright.stop()
            except Exception:
                pass
        if acquired_port is not None:
            released = pool.release(acquired_port)
            if released.get("status") == "released":
                print(f"Released Chrome CDP port {acquired_port}")
            else:
                print(f"CDP port release warning: {released.get('error', released)}")
        _print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())
