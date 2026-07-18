"""Resumable eBay detail-page gallery URL collector using Armada Chrome CDP."""

from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, Playwright, TimeoutError as PlaywrightTimeoutError, async_playwright


REPO_ROOT = Path(__file__).resolve().parent
NODE_MCP_DIR = REPO_ROOT / "node-mcp-server"
if str(NODE_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(NODE_MCP_DIR))

from cdp_pool import ensure_initialized, pool  # noqa: E402


EBAY_HOME_URL = "https://www.ebay.com"
RESULTS_PATH = REPO_ROOT / "ebay_scrape_results.json"
STATS_PATH = REPO_ROOT / "ebay_image_stats.json"
NAVIGATION_TIMEOUT_MS = 30_000
POST_LOAD_WAIT_MS = 3_000
DETAIL_PACE_MS = 4_000
SAVE_INTERVAL = 50
IMAGE_HASH_PATTERN = re.compile(r"https://i\.ebayimg\.com/images/g/([^/]+)/")


def _load_results() -> dict[str, Any]:
    with RESULTS_PATH.open(encoding="utf-8") as source:
        payload = json.load(source)
    if not isinstance(payload, dict) or not isinstance(payload.get("listings"), list):
        raise ValueError(f"{RESULTS_PATH} must contain an object with a listings array")
    return payload


def _stats(payload: dict[str, Any], runtime_seconds: float) -> dict[str, Any]:
    listings = payload["listings"]
    gallery_urls = [listing.get("gallery_urls") or [] for listing in listings if "gallery_urls" in listing]
    total_image_count = sum(len(urls) for urls in gallery_urls)
    unique_images = {url for urls in gallery_urls for url in urls}
    listings_with_images = sum(1 for urls in gallery_urls if urls)
    listings_failed = sum(
        1
        for listing in listings
        if listing.get("gallery_error") or ("gallery_urls" in listing and not listing["gallery_urls"])
    )
    total_listings = len(listings)
    return {
        "total_listings": total_listings,
        "listings_with_images": listings_with_images,
        "listings_failed": listings_failed,
        "avg_images_per_listing": round(total_image_count / total_listings, 2) if total_listings else 0,
        "total_unique_images": len(unique_images),
        "runtime_seconds": round(runtime_seconds, 2),
    }


def _save_progress(payload: dict[str, Any], runtime_seconds: float) -> None:
    results_temporary = RESULTS_PATH.with_suffix(".json.tmp")
    stats_temporary = STATS_PATH.with_suffix(".json.tmp")
    results_temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    stats_temporary.write_text(json.dumps(_stats(payload, runtime_seconds), indent=2), encoding="utf-8")
    results_temporary.replace(RESULTS_PATH)
    stats_temporary.replace(STATS_PATH)


def _gallery_urls(html: str) -> list[str]:
    seen_hashes: set[str] = set()
    gallery_urls: list[str] = []
    for image_hash in IMAGE_HASH_PATTERN.findall(html):
        if image_hash in seen_hashes:
            continue
        seen_hashes.add(image_hash)
        gallery_urls.append(f"https://i.ebayimg.com/images/g/{image_hash}/s-l1600.jpg")
    return gallery_urls


async def _navigate(page: Page, url: str) -> int | None:
    response = await page.goto(url, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)
    await page.wait_for_timeout(POST_LOAD_WAIT_MS)
    return response.status if response is not None else None


async def _fetch_gallery_urls(context: BrowserContext, item_url: str) -> tuple[list[str] | None, str | None]:
    page: Page | None = None
    try:
        page = await context.new_page()
        page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
        response_status = await _navigate(page, item_url)
        if response_status is not None and response_status >= 400:
            return None, f"Detail navigation returned HTTP {response_status}"
        return _gallery_urls(await page.content()), None
    except PlaywrightTimeoutError as exc:
        return None, f"Detail navigation timed out: {exc}"
    except Exception as exc:
        return None, f"Detail navigation failed: {exc}"
    finally:
        if page is not None:
            try:
                await page.close()
            except Exception:
                pass


def _print_progress(completed: int, total: int, started_at: float, image_count: int) -> None:
    elapsed = time.monotonic() - started_at
    average = elapsed / completed if completed else 0
    print(f"[{completed}/{total}] avg {average:.1f}s/listing, {image_count} images found")


def _print_summary(stats: dict[str, Any]) -> None:
    total = stats["total_listings"]
    success_rate = (stats["listings_with_images"] / total * 100) if total else 0
    print("\nGallery scrape summary")
    print(f"  Total listings: {total}")
    print(f"  Listings with images: {stats['listings_with_images']} ({success_rate:.1f}%)")
    print(f"  Listings failed or empty: {stats['listings_failed']}")
    print(f"  Average images per listing: {stats['avg_images_per_listing']}")
    print(f"  Unique images: {stats['total_unique_images']}")
    print(f"  Runtime: {stats['runtime_seconds']}s")
    print(f"  Stats: {STATS_PATH}")


async def main() -> None:
    started_at = time.monotonic()
    payload: dict[str, Any] | None = None
    playwright: Playwright | None = None
    browser: Browser | None = None
    context: BrowserContext | None = None
    homepage: Page | None = None
    created_context = False
    acquired_port: int | None = None

    try:
        payload = _load_results()
        listings: list[dict[str, Any]] = payload["listings"]
        pending = [listing for listing in listings if "gallery_urls" not in listing]
        print(f"Loaded {len(listings)} listings; {len(pending)} need gallery extraction")
        if not pending:
            return

        ensure_initialized()
        acquired = pool.acquire("ebay-image-scraper")
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

        homepage = await context.new_page()
        homepage.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
        try:
            await _navigate(homepage, EBAY_HOME_URL)
            print("eBay homepage loaded; detail session established")
        except Exception as exc:
            print(f"Homepage navigation failed; continuing with detail pages: {exc}")
        finally:
            try:
                await homepage.close()
            except Exception:
                pass
            homepage = None

        already_processed = len(listings) - len(pending)
        checkpoint_count = 0
        for index, listing in enumerate(pending, start=1):
            item_url = listing.get("item_url")
            if not item_url:
                listing["gallery_urls"] = []
                listing["gallery_count"] = 0
                listing["gallery_error"] = "Listing did not include an item URL"
                image_count = 0
                print(f"[{index}/{len(pending)}] missing item URL")
            else:
                gallery_urls, error = await _fetch_gallery_urls(context, str(item_url))
                if error:
                    listing["gallery_error"] = error
                    image_count = 0
                    print(f"[{index}/{len(pending)}] {listing.get('item_id') or item_url}: {error}")
                else:
                    listing["gallery_urls"] = gallery_urls or []
                    listing["gallery_count"] = len(listing["gallery_urls"])
                    listing.pop("gallery_error", None)
                    image_count = listing["gallery_count"]
                    if image_count == 0:
                        print(f"[{index}/{len(pending)}] {listing.get('item_id') or item_url}: 0 image hashes found")

            checkpoint_count += 1
            if checkpoint_count >= SAVE_INTERVAL:
                _save_progress(payload, time.monotonic() - started_at)
                checkpoint_count = 0
            if index % 10 == 0:
                _print_progress(already_processed + index, len(listings), started_at, image_count)
            if index < len(pending):
                await asyncio.sleep(DETAIL_PACE_MS / 1000)
    except KeyboardInterrupt:
        print("Interrupted; preserving current gallery progress.")
    except Exception as exc:
        print(f"Gallery scraper setup failed: {exc}")
    finally:
        runtime_seconds = time.monotonic() - started_at
        if payload is not None:
            _save_progress(payload, runtime_seconds)
        if homepage is not None:
            try:
                await homepage.close()
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
        if payload is not None:
            _print_summary(_stats(payload, runtime_seconds))


if __name__ == "__main__":
    asyncio.run(main())
