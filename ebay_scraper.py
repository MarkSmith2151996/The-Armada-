from __future__ import annotations

import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import Browser, BrowserContext, Page, Playwright, TimeoutError as PlaywrightTimeoutError, async_playwright


REPO_ROOT = Path(__file__).resolve().parent
NODE_MCP_DIR = REPO_ROOT / "node-mcp-server"
if str(NODE_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(NODE_MCP_DIR))

from cdp_pool import ensure_initialized, pool  # noqa: E402


SEARCH_URL = "https://www.ebay.com/sch/i.html?_nkw=motherboard&LH_ItemCondition=7000&_sop=10&_ipg=240"
RESULTS_PATH = REPO_ROOT / "ebay_scrape_results.json"
SEARCH_DEBUG_PATH = REPO_ROOT / "debug_search_page.html"
DETAIL_DEBUG_PATH = REPO_ROOT / "debug_detail_page.html"
NAVIGATION_TIMEOUT_MS = 45_000
NETWORK_IDLE_TIMEOUT_MS = 10_000
POST_LOAD_WAIT_MS = 2_500
DETAIL_DELAY_SECONDS = 4

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
        text = _node_text(root.select_one(selector))
        if text:
            return text
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


def _absolute_url(value: str | None, base_url: str) -> str | None:
    if not value or value.startswith("data:"):
        return None
    return urljoin(base_url, value)


def _item_id(item_url: str | None) -> str | None:
    if not item_url:
        return None
    match = re.search(r"/itm/(?:[^/?#]+/)?(\d{9,})", item_url)
    return match.group(1) if match else None


def _listing_type(card: Any) -> str:
    text = (_node_text(card) or "").lower()
    if "best offer" in text:
        return "best_offer"
    if "auction" in text or re.search(r"\b\d[\d,]*\s+bids?\b", text):
        return "auction"
    return "buy_it_now"


def _extract_search_listings(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    listings: list[dict[str, Any]] = []

    for card in soup.select(".s-item"):
        title = _first_text(card, (".s-item__title [role='heading']", ".s-item__title", "[role='heading']"))
        if not title or "shop on ebay" in title.lower():
            continue

        raw_url = _first_attribute(card, ("a.s-item__link[href]", "a[href*='/itm/']"), ("href",))
        item_url = _absolute_url(raw_url, SEARCH_URL)
        thumbnail_url = _absolute_url(
            _first_attribute(
                card,
                (".s-item__image img", "img.s-item__image-img", "img"),
                ("data-src", "data-original", "src"),
            ),
            SEARCH_URL,
        )
        seller_name = _first_text(
            card,
            (".s-item__seller-info-text", ".s-item__seller-info", "[data-testid*='seller']"),
        )
        if seller_name:
            seller_name = re.sub(r"^seller:\s*", "", seller_name, flags=re.IGNORECASE)

        listings.append(
            {
                "item_id": _item_id(item_url),
                "title": title,
                "price": _first_text(card, (".s-item__price", "[data-testid*='price']")),
                "condition": _first_text(card, (".SECONDARY_INFO", ".s-item__subtitle", "[data-testid*='condition']")),
                "listing_type": _listing_type(card),
                "shipping_cost": _first_text(card, (".s-item__shipping", ".s-item__logisticsCost", "[data-testid*='shipping']")),
                "seller_name": seller_name,
                "item_url": item_url,
                "thumbnail_url": thumbnail_url,
            }
        )

    return listings


def _is_bot_detection_page(html: str) -> bool:
    lowered = html.lower()
    return any(marker in lowered for marker in BOT_DETECTION_MARKERS)


def _empty_detail_data() -> dict[str, Any]:
    return {
        "title": None,
        "image_urls": None,
        "description": None,
        "item_specifics": None,
        "seller": {
            "name": None,
            "feedback_score": None,
            "feedback_percentage": None,
        },
        "location": None,
        "bid_count": None,
        "end_date": None,
        "condition_description": None,
    }


def _iter_json_values(value: Any, target_keys: set[str]) -> list[str]:
    values: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key.lower() in target_keys:
                if isinstance(nested, str):
                    values.append(nested)
                elif isinstance(nested, list):
                    values.extend(item for item in nested if isinstance(item, str))
            values.extend(_iter_json_values(nested, target_keys))
    elif isinstance(value, list):
        for nested in value:
            values.extend(_iter_json_values(nested, target_keys))
    return values


def _json_ld_payloads(soup: BeautifulSoup) -> list[Any]:
    payloads: list[Any] = []
    for node in soup.select("script[type='application/ld+json']"):
        raw = node.string or node.get_text()
        if not raw:
            continue
        try:
            payloads.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return payloads


def _attribute_urls(value: str) -> list[str]:
    return [part.strip().split()[0] for part in value.split(",") if part.strip()]


def _full_resolution_ebay_image(value: str) -> str | None:
    normalized = value.replace("\\/", "/")
    if normalized.startswith("//"):
        normalized = f"https:{normalized}"
    if not normalized.startswith(("http://", "https://")) or "ebayimg.com" not in normalized:
        return None
    return re.sub(r"/s-l\d+(?=\.)", "/s-l1600", normalized)


def _extract_image_urls(soup: BeautifulSoup) -> list[str] | None:
    candidates: list[str] = []
    gallery_selectors = (
        "#PicturePanel img",
        ".ux-image-carousel img",
        ".ux-image-filmstrip img",
        "#vi_main_img_fs img",
        "#icImg",
        "[data-testid*='gallery'] img",
    )
    for selector in gallery_selectors:
        for image in soup.select(selector):
            for attribute in ("data-zoom-src", "data-zoom", "data-src", "src", "srcset"):
                value = image.get(attribute)
                if not value:
                    continue
                candidates.extend(_attribute_urls(str(value)) if attribute == "srcset" else [str(value)])

    for image in soup.select("[data-zoom-src], [data-zoom]"):
        for attribute in ("data-zoom-src", "data-zoom"):
            value = image.get(attribute)
            if value:
                candidates.append(str(value))

    for payload in _json_ld_payloads(soup):
        candidates.extend(_iter_json_values(payload, {"image", "imageurl", "contenturl"}))

    image_urls: list[str] = []
    for candidate in candidates:
        image_url = _full_resolution_ebay_image(candidate)
        if image_url and image_url not in image_urls:
            image_urls.append(image_url)
    return image_urls or None


def _extract_item_specifics(soup: BeautifulSoup) -> dict[str, str] | None:
    specifics: dict[str, str] = {}

    def add_pair(label: str | None, value: str | None) -> None:
        if not label or not value:
            return
        key = label.rstrip(": ")
        if key and key not in specifics:
            specifics[key] = value

    for row in soup.select(".ux-labels-values"):
        add_pair(
            _first_text(row, (".ux-labels-values__labels", "dt", "th")),
            _first_text(row, (".ux-labels-values__values", "dd", "td")),
        )

    for row in soup.select(".itemAttr tr, [data-testid*='item-specific'] tr"):
        cells = row.select("th, td")
        if len(cells) >= 2:
            add_pair(_node_text(cells[0]), _node_text(cells[1]))

    for definition in soup.select(".itemAttr dl, [data-testid*='item-specific'] dl"):
        add_pair(_node_text(definition.select_one("dt")), _node_text(definition.select_one("dd")))

    return specifics or None


def _walk_dicts(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        found = [value]
        for nested in value.values():
            found.extend(_walk_dicts(nested))
        return found
    if isinstance(value, list):
        found: list[dict[str, Any]] = []
        for nested in value:
            found.extend(_walk_dicts(nested))
        return found
    return []


def _extract_seller(soup: BeautifulSoup) -> dict[str, str | None]:
    seller = {"name": None, "feedback_score": None, "feedback_percentage": None}
    container = soup.select_one(".x-sellercard-atf, .si-content, [data-testid*='seller-card']")
    seller_text = _node_text(container)
    if container is not None:
        seller["name"] = _first_text(
            container,
            (
                "a[href*='/usr/']",
                ".x-sellercard-atf__info__about-seller",
                ".x-sellercard-atf__info__seller",
            ),
        )

    if not seller["name"]:
        for payload in _json_ld_payloads(soup):
            for candidate in _walk_dicts(payload):
                source = candidate.get("seller")
                if isinstance(source, dict) and source.get("name"):
                    seller["name"] = _clean_text(str(source["name"]))
                    break
            if seller["name"]:
                break

    if seller["name"]:
        seller["name"] = re.sub(r"\s*\([\d,.]+\)\s*$", "", seller["name"])

    if seller_text:
        percentage = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:positive\s*)?feedback", seller_text, re.IGNORECASE)
        score = re.search(r"\b([\d,]+)\s+feedback(?:\s+score)?\b", seller_text, re.IGNORECASE)
        if percentage:
            seller["feedback_percentage"] = f"{percentage.group(1)}%"
        if score:
            seller["feedback_score"] = score.group(1)

    return seller


def _extract_location(soup: BeautifulSoup, specifics: dict[str, str] | None) -> str | None:
    if specifics:
        for label, value in specifics.items():
            if "location" in label.lower():
                return value

    text = soup.get_text("\n", strip=True)
    match = re.search(r"(?:located in|item location)\s*:\s*([^\n]+)", text, re.IGNORECASE)
    return _clean_text(match.group(1)) if match else None


def _extract_bid_count(soup: BeautifulSoup) -> int | None:
    for node in soup.select(".x-bid-count, [class*='bid-count'], [data-testid*='bid']"):
        match = re.search(r"\b([\d,]+)\s+bids?\b", _node_text(node) or "", re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
    return None


def _extract_end_date(soup: BeautifulSoup) -> str | None:
    return _first_text(
        soup,
        (
            ".x-end-date-primary",
            ".x-end-date",
            "#vi-cdown_timeLeft",
            "[data-testid*='end-date']",
            "[class*='end-date']",
        ),
    )


def _extract_detail_data(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    detail = _empty_detail_data()
    specifics = _extract_item_specifics(soup)
    detail["title"] = _first_text(soup, ("h1.x-item-title__mainTitle", "h1"))
    detail["image_urls"] = _extract_image_urls(soup)
    detail["description"] = _first_text(
        soup,
        (".d-item-description", "#desc_div", "#viTabs_0_is", "[data-testid*='item-description']"),
    )
    detail["item_specifics"] = specifics
    detail["seller"] = _extract_seller(soup)
    detail["location"] = _extract_location(soup, specifics)
    detail["bid_count"] = _extract_bid_count(soup)
    detail["end_date"] = _extract_end_date(soup)
    detail["condition_description"] = _first_text(
        soup,
        (
            ".x-item-condition-max-view__description",
            ".x-item-condition__description",
            "[data-testid*='condition-description']",
        ),
    )
    return detail


async def _extract_description_frame(page: Page) -> str | None:
    for frame in page.frames:
        if frame == page.main_frame or "ebaydesc" not in frame.url.lower():
            continue
        try:
            frame_html = await frame.content()
        except Exception:
            continue
        description = _clean_text(BeautifulSoup(frame_html, "html.parser").get_text(" ", strip=True))
        if description:
            return description
    return None


async def _navigate(page: Page, url: str) -> int | None:
    response = await page.goto(url, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)
    try:
        await page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        pass
    await page.wait_for_timeout(POST_LOAD_WAIT_MS)
    return response.status if response is not None else None


async def _scrape_detail(context: BrowserContext, item_url: str) -> tuple[dict[str, Any], str, str | None]:
    page: Page | None = None
    html = ""
    try:
        page = await context.new_page()
        page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
        response_status = await _navigate(page, item_url)
        html = await page.content()
        if _is_bot_detection_page(html):
            return _empty_detail_data(), html, "eBay CAPTCHA or bot-detection page detected"

        detail = _extract_detail_data(html)
        if detail["description"] is None:
            detail["description"] = await _extract_description_frame(page)
        if response_status is not None and response_status >= 400:
            return detail, html, f"Detail navigation returned HTTP {response_status}"
        return detail, html, None
    except Exception as exc:
        if page is not None and not html:
            try:
                html = await page.content()
            except Exception:
                pass
        return _empty_detail_data(), html, f"Detail navigation failed: {exc}"
    finally:
        if page is not None:
            try:
                await page.close()
            except Exception:
                pass


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _is_populated(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, list, dict)):
        return bool(value)
    return True


def _print_summary(results: dict[str, Any]) -> None:
    listings = results["listings"]
    print(f"Total listings: {results['total_found']}")
    print("Sample titles:")
    for listing in listings[:5]:
        print(f"  - {listing['search_data']['title']}")

    search_fields = ("item_id", "title", "price", "condition", "listing_type", "shipping_cost", "seller_name", "item_url", "thumbnail_url")
    print("Search fields populated:")
    for field in search_fields:
        count = sum(_is_populated(listing["search_data"].get(field)) for listing in listings)
        print(f"  {field}: {count}/{len(listings)}")

    detailed = [listing["detail_data"] for listing in listings if "detail_data" in listing]
    if detailed:
        detail_fields = ("title", "image_urls", "description", "item_specifics", "location", "bid_count", "end_date", "condition_description")
        print("Detail fields populated:")
        for field in detail_fields:
            count = sum(_is_populated(detail.get(field)) for detail in detailed)
            print(f"  {field}: {count}/{len(detailed)}")
        for field in ("name", "feedback_score", "feedback_percentage"):
            count = sum(_is_populated(detail["seller"].get(field)) for detail in detailed)
            print(f"  seller.{field}: {count}/{len(detailed)}")

    missing_search = [
        field
        for field in search_fields
        if any(not _is_populated(listing["search_data"].get(field)) for listing in listings)
    ]
    missing_detail = [
        field
        for field in ("title", "image_urls", "description", "item_specifics", "location", "bid_count", "end_date", "condition_description")
        if detailed and any(not _is_populated(detail.get(field)) for detail in detailed)
    ]
    print(f"Search fields with missing values: {', '.join(missing_search) if missing_search else 'none'}")
    print(f"Detail fields with missing values: {', '.join(missing_detail) if missing_detail else 'none'}")

    errors = [listing["detail_error"] for listing in listings if listing.get("detail_error")]
    if errors:
        print("Detail fetch errors:")
        for error in errors:
            print(f"  - {error}")


async def main() -> None:
    results: dict[str, Any] = {
        "scrape_time": datetime.now(timezone.utc).isoformat(),
        "search_url": SEARCH_URL,
        "total_found": 0,
        "listings": [],
    }
    playwright: Playwright | None = None
    browser: Browser | None = None
    context: BrowserContext | None = None
    search_page: Page | None = None
    created_context = False
    acquired_port: int | None = None
    search_html = ""
    detail_debug_written = False

    try:
        ensure_initialized()
        acquired = pool.acquire("ebay-scraper")
        if acquired.get("status") != "acquired":
            raise RuntimeError(str(acquired.get("error") or "No CDP pool slot is available"))
        acquired_port = int(acquired["port"])
        cdp_endpoint = f"http://localhost:{acquired_port}"
        print(f"Acquired Chrome CDP port {acquired_port}")

        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(cdp_endpoint)
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = await browser.new_context()
            created_context = True

        search_page = await context.new_page()
        search_page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
        try:
            search_status = await _navigate(search_page, SEARCH_URL)
            try:
                await search_page.wait_for_selector(".s-item", state="attached", timeout=15_000)
            except PlaywrightTimeoutError:
                pass
            search_html = await search_page.content()
            _write_text(SEARCH_DEBUG_PATH, search_html)
            if _is_bot_detection_page(search_html):
                print("eBay CAPTCHA or bot-detection page detected on the search page.")
            else:
                if search_status is not None and search_status >= 400:
                    print(f"Search navigation returned HTTP {search_status}; attempting to parse the response.")
                search_listings = _extract_search_listings(search_html)
                results["listings"] = [{"search_data": listing} for listing in search_listings]
                results["total_found"] = len(search_listings)
                print(f"Listings found: {len(search_listings)}")

                for index, listing in enumerate(results["listings"][:5], start=1):
                    item_url = listing["search_data"].get("item_url")
                    if not item_url:
                        listing["detail_data"] = _empty_detail_data()
                        listing["detail_error"] = "Listing did not include an item URL"
                        continue
                    detail_data, detail_html, error = await _scrape_detail(context, item_url)
                    listing["detail_data"] = detail_data
                    if error:
                        listing["detail_error"] = error
                        print(f"Detail {index} failed: {error}")
                    if not detail_debug_written and detail_html:
                        _write_text(DETAIL_DEBUG_PATH, detail_html)
                        detail_debug_written = True
                    if index < min(5, len(results["listings"])):
                        await asyncio.sleep(DETAIL_DELAY_SECONDS)
        except Exception as exc:
            print(f"Search navigation failed: {exc}")
            if search_page is not None and not search_html:
                try:
                    search_html = await search_page.content()
                except Exception:
                    pass
    except Exception as exc:
        print(f"Scraper setup failed: {exc}")
    finally:
        if not search_html:
            search_html = "<!-- Search page HTML could not be retrieved. See stdout for the navigation error. -->"
        if not SEARCH_DEBUG_PATH.exists():
            _write_text(SEARCH_DEBUG_PATH, search_html)
        if not detail_debug_written and results["listings"]:
            _write_text(DETAIL_DEBUG_PATH, "<!-- Detail page HTML could not be retrieved. See stdout for the navigation error. -->")

        if search_page is not None:
            try:
                await search_page.close()
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
            if released.get("status") != "released":
                print(f"CDP port release warning: {released.get('error', released)}")
            else:
                print(f"Released Chrome CDP port {acquired_port}")

        RESULTS_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        _print_summary(results)
        print(f"Wrote results: {RESULTS_PATH}")
        print(f"Wrote search debug HTML: {SEARCH_DEBUG_PATH}")
        if DETAIL_DEBUG_PATH.exists():
            print(f"Wrote detail debug HTML: {DETAIL_DEBUG_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
