"""Look up sold eBay comps for bent-pin listings and store their flip margin."""

from __future__ import annotations

import json
import random
import re
import statistics
import time
import unicodedata
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import psycopg2
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import BrowserContext, Page, sync_playwright


CDP_URL = "http://127.0.0.1:9224"
DB_CONFIG = {
    "host": "172.17.0.1",
    "port": 5432,
    "dbname": "hive",
    "user": "fba_writer",
    "password": "fba_pipeline_2026",
}
RESULTS_PATH = Path(__file__).resolve().with_name("ebay_price_lookups.json")
LOOKUP_QUERY = """
SELECT item_id, title, price
FROM ebay.listings
WHERE LOWER(title) LIKE '%bent pin%'
   OR LOWER(title) LIKE '%bent cpu%'
   OR LOWER(title) LIKE '%pins bent%'
   OR LOWER(title) LIKE '%pin damage%'
   OR LOWER(title) LIKE '%pins broken%'
   OR LOWER(title) LIKE '%bent socket%'
ORDER BY price DESC
"""
UPDATE_LISTING = """
UPDATE ebay.listings
SET market_price = %s,
    spread = %s,
    spread_pct = %s
WHERE item_id = %s
"""

BRACKETED_TEXT = re.compile(r"\[[^]]*\]|\([^)]*\)")
DAMAGE_TEXT = re.compile(
    r"\b(?:"
    r"bent\s+(?:cpu\s+)?pins?|pins?\s+bent|pins?\s+broken|pin\s+damage|"
    r"bent\s+socket|for\s+parts(?:\s+(?:or\s+)?repair)?|parts\s+only|"
    r"not\s+working|as[-\s]?is|repair|broken|defective|damaged|faulty|"
    r"untested|no\s+power|read\s+(?:the\s+)?description|see\s+description"
    r")\b",
    re.IGNORECASE,
)
MARKUP_NOISE = re.compile(r"\*+|[|_~]+")
SEPARATOR_NOISE = re.compile(r"\s*[-,:;/]+\s*")
WHITESPACE = re.compile(r"\s+")
PRICE_PATTERN = re.compile(r"(?:US\s*)?\$\s*([\d,]+(?:\.\d{1,2})?)", re.IGNORECASE)


def log(message: str) -> None:
    print(message, flush=True)


def extract_model(title: str) -> str:
    """Remove damage descriptions and seller clutter while retaining a usable search query."""
    without_emoji = "".join(
        character
        for character in title
        if unicodedata.category(character) not in {"So", "Cs"}
    )
    model = BRACKETED_TEXT.sub(" ", without_emoji)
    model = DAMAGE_TEXT.sub(" ", model)
    model = MARKUP_NOISE.sub(" ", model)
    model = SEPARATOR_NOISE.sub(" ", model)
    return WHITESPACE.sub(" ", model).strip(" -,:;/")


def parse_price(value: str) -> float | None:
    match = PRICE_PATTERN.search(value)
    if not match:
        return None
    try:
        return float(Decimal(match.group(1).replace(",", "")))
    except ArithmeticError:
        return None


def sold_search_url(model_query: str) -> str:
    return "https://www.ebay.com/sch/i.html?" + urlencode(
        {
            "_nkw": model_query,
            "LH_ItemCondition": "3000",
            "_sop": "12",
            "LH_Complete": "1",
            "LH_Sold": "1",
        }
    )


def extract_sold_prices(page: Page) -> list[float]:
    """Read the first ten sold-card price areas, with a card-wide fallback for markup changes."""
    card_texts = page.locator("ul.srp-results .s-card").evaluate_all(
        """
        cards => cards.slice(0, 10).map(card => {
            const attributes = card.querySelector('.su-card-container__attributes');
            const price = card.querySelector('.s-card__price');
            return (attributes || price || card).innerText || '';
        })
        """
    )
    prices = [price for text in card_texts if (price := parse_price(text)) is not None]
    return prices[:10]


def lookup_sold_prices(context: BrowserContext, model_query: str) -> list[float]:
    page = context.new_page()
    try:
        page.goto(sold_search_url(model_query), wait_until="domcontentloaded", timeout=45_000)
        page.wait_for_selector("ul.srp-results, .s-card", timeout=20_000)
        return extract_sold_prices(page)
    finally:
        page.close()


def save_results(results: list[dict[str, Any]]) -> None:
    with RESULTS_PATH.open("w", encoding="utf-8") as output:
        json.dump(results, output, indent=2)
        output.write("\n")


def update_listing(connection: Any, item_id: str, market_price: float | None, net_spread: float | None, spread_pct: float | None) -> None:
    with connection.cursor() as cursor:
        cursor.execute(UPDATE_LISTING, (market_price, net_spread, spread_pct, item_id))
    connection.commit()


def make_result(item_id: str, title: str, broken_price: float | None, model_query: str) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "title": title,
        "broken_price": broken_price,
        "model_query": model_query,
        "sold_prices": [],
        "market_price_low": None,
        "market_price_median": None,
        "market_price_high": None,
        "gross_spread": None,
        "net_spread": None,
        "spread_pct": None,
    }


def print_progress(index: int, total: int, result: dict[str, Any]) -> None:
    model = str(result["model_query"])[:55] or "no model extracted"
    broken_price = result["broken_price"]
    working_price = result["market_price_median"]
    net_spread = result["net_spread"]
    spread_pct = result["spread_pct"]
    if all(value is not None for value in (broken_price, working_price, net_spread, spread_pct)):
        log(
            f"[{index}/{total}] {model}: broken=${broken_price:.2f} "
            f"-> working=${working_price:.2f} -> spread=${net_spread:.2f} ({spread_pct:.0f}%)"
        )
    else:
        log(f"[{index}/{total}] {model}: no sold comps")


def run() -> int:
    results: list[dict[str, Any]] = []
    with psycopg2.connect(**DB_CONFIG) as connection:
        with connection.cursor() as cursor:
            cursor.execute(LOOKUP_QUERY)
            listings = cursor.fetchall()

        total = len(listings)
        log(f"Found {total} bent-pin listings")
        save_results(results)
        if not listings:
            log("eBay price lookup summary")
            log("  Total looked up: 0")
            log("  Found comps for: 0.0%")
            log("  Average net spread: n/a")
            return 0

        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(CDP_URL)
            if not browser.contexts:
                raise RuntimeError(f"No browser context is available at {CDP_URL}")
            context = browser.contexts[0]
            homepage = context.new_page()
            try:
                homepage.goto("https://www.ebay.com/", wait_until="domcontentloaded", timeout=45_000)
            finally:
                homepage.close()

            for index, (item_id, title, price) in enumerate(listings, start=1):
                broken_price = float(price) if price is not None else None
                model_query = extract_model(str(title))
                result = make_result(str(item_id), str(title), broken_price, model_query)

                try:
                    if not model_query:
                        raise ValueError("model extraction produced an empty query")
                    if broken_price is None:
                        raise ValueError("listing does not have a broken price")

                    sold_prices = lookup_sold_prices(context, model_query)
                    result["sold_prices"] = sold_prices
                    if sold_prices:
                        market_price_low = min(sold_prices)
                        market_price_median = float(statistics.median(sold_prices))
                        market_price_high = max(sold_prices)
                        gross_spread = market_price_median - broken_price
                        net_spread = gross_spread - (market_price_median * 0.13) - 15
                        spread_pct = (net_spread / broken_price) * 100
                        result.update(
                            market_price_low=market_price_low,
                            market_price_median=market_price_median,
                            market_price_high=market_price_high,
                            gross_spread=gross_spread,
                            net_spread=net_spread,
                            spread_pct=spread_pct,
                        )
                        update_listing(connection, str(item_id), market_price_median, net_spread, spread_pct)
                    else:
                        update_listing(connection, str(item_id), None, None, None)
                        log(f"[{index}/{total}] {model_query}: 0 sold results")
                except (PlaywrightTimeoutError, PlaywrightError, ValueError, psycopg2.Error) as exc:
                    connection.rollback()
                    result["error"] = str(exc)
                    log(f"[{index}/{total}] {model_query or title}: skipped: {exc}")
                except Exception as exc:
                    connection.rollback()
                    result["error"] = str(exc)
                    log(f"[{index}/{total}] {model_query or title}: unexpected error: {exc}")
                finally:
                    results.append(result)
                    if index % 5 == 0 or index == total:
                        print_progress(index, total, result)
                    if index % 10 == 0:
                        save_results(results)

                if index < total:
                    time.sleep(random.uniform(5, 8))

    save_results(results)
    comp_results = [result for result in results if result["market_price_median"] is not None]
    net_spreads = [float(result["net_spread"]) for result in comp_results]
    log("eBay price lookup summary")
    log(f"  Total looked up: {len(results)}")
    log(f"  Found comps for: {(len(comp_results) / len(results) * 100):.1f}%")
    log(f"  Average net spread: ${statistics.mean(net_spreads):.2f}" if net_spreads else "  Average net spread: n/a")
    log("  Best deals:")
    for result in sorted(comp_results, key=lambda item: float(item["spread_pct"]), reverse=True)[:5]:
        log(
            f"    {result['model_query'][:55]}: ${result['net_spread']:.2f} "
            f"({result['spread_pct']:.1f}%)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
