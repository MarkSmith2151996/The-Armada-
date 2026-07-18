"""Resumable eBay detail-page gallery image collector."""

from __future__ import annotations

import asyncio
import json
import random
import re
import time
from pathlib import Path
from typing import Any

from playwright.async_api import (
    BrowserContext,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)


REPO_ROOT = Path(__file__).resolve().parent
RESULTS_PATH = REPO_ROOT / "ebay_scrape_results.json"
NAVIGATION_TIMEOUT_MS = 30_000
POST_LOAD_WAIT_MS = 3_000
SAVE_INTERVAL = 25
ERROR_PAGE_MARKERS = (
    "pardon our interruption",
    "access denied",
    "request blocked",
    "temporarily unavailable",
)


def _load_results() -> dict[str, Any]:
    with RESULTS_PATH.open(encoding="utf-8") as source:
        payload = json.load(source)
    if not isinstance(payload, dict) or not isinstance(payload.get("listings"), list):
        raise ValueError(f"{RESULTS_PATH} must contain an object with a listings array")
    return payload


def _save_results(payload: dict[str, Any]) -> None:
    temporary_path = RESULTS_PATH.with_name(f"{RESULTS_PATH.name}.tmp")
    temporary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary_path.replace(RESULTS_PATH)


def _extract_gallery_urls(html: str) -> list[str]:
    hashes: set[str] = set()
    gallery_urls: list[str] = []
    for image_hash in re.findall(r"/images/g/([^/]+)/", html):
        if image_hash not in hashes:
            hashes.add(image_hash)
            gallery_urls.append(f"https://i.ebayimg.com/images/g/{image_hash}/s-l1600.jpg")
    return gallery_urls


def _is_error_page(html: str) -> bool:
    normalized_html = html.lower()
    return any(marker in normalized_html for marker in ERROR_PAGE_MARKERS)


async def _fetch_gallery_urls(context: BrowserContext, item_url: str) -> tuple[list[str], str | None]:
    page: Page | None = None
    try:
        page = await context.new_page()
        page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
        response = await page.goto(item_url, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)
        await page.wait_for_timeout(POST_LOAD_WAIT_MS)
        response_status = response.status if response is not None else None
        if response_status == 403 or (response_status is not None and response_status >= 400):
            return [], f"Detail navigation returned HTTP {response_status}"

        html = await page.content()
        if _is_error_page(html):
            return [], "eBay returned an error page"
        return _extract_gallery_urls(html), None
    except PlaywrightTimeoutError:
        return [], "Detail navigation timed out"
    except Exception as exc:
        return [], f"Detail navigation failed: {exc}"
    finally:
        if page is not None:
            try:
                await page.close()
            except Exception:
                pass


def _set_failure(listing: dict[str, Any], error: str) -> None:
    listing["gallery_urls"] = []
    listing["gallery_count"] = 0
    listing["gallery_error"] = error


def _print_summary(payload: dict[str, Any], runtime_seconds: float) -> None:
    listings: list[dict[str, Any]] = payload["listings"]
    processed = [listing for listing in listings if "gallery_urls" in listing]
    image_lists = [listing.get("gallery_urls") or [] for listing in processed]
    total_images = sum(len(urls) for urls in image_lists)
    unique_images = {url for urls in image_lists for url in urls}
    successful_listings = sum(1 for urls in image_lists if urls)
    success_rate = successful_listings / len(processed) * 100 if processed else 0
    average_images = total_images / len(processed) if processed else 0

    print("\nGallery scrape summary", flush=True)
    print(f"Total processed: {len(processed)}/{len(listings)}", flush=True)
    print(f"Success rate: {success_rate:.1f}%", flush=True)
    print(f"Average images per listing: {average_images:.1f}", flush=True)
    print(f"Total unique images: {len(unique_images)}", flush=True)
    print(f"Runtime: {runtime_seconds:.1f}s", flush=True)


async def main() -> None:
    started_at = time.monotonic()
    payload: dict[str, Any] | None = None
    playwright: Playwright | None = None
    homepage: Page | None = None
    created_context: BrowserContext | None = None

    try:
        payload = _load_results()
        listings: list[dict[str, Any]] = payload["listings"]
        remaining = [listing for listing in listings if "gallery_urls" not in listing]
        already_done = len(listings) - len(remaining)
        print(f"Loaded {len(listings)} listings", flush=True)
        print(f"Resuming: {already_done} already done, {len(remaining)} remaining", flush=True)
        if not remaining:
            return

        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9223")
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = await browser.new_context()
            created_context = context

        homepage = await context.new_page()
        homepage.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
        try:
            await homepage.goto("https://www.ebay.com", wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)
            await homepage.wait_for_timeout(POST_LOAD_WAIT_MS)
            print("eBay homepage loaded; detail session established", flush=True)
        except Exception as exc:
            print(f"Homepage navigation failed; continuing with detail pages: {exc}", flush=True)
        finally:
            try:
                await homepage.close()
            except Exception:
                pass
            homepage = None

        processed_this_run = 0
        for listing in remaining:
            item_url = listing.get("item_url")
            listing_label = str(listing.get("item_id") or item_url or "unknown listing")
            if not item_url:
                _set_failure(listing, "Listing did not include an item URL")
                image_count = 0
                print(f"{listing_label}: missing item URL", flush=True)
            else:
                gallery_urls, error = await _fetch_gallery_urls(context, str(item_url))
                if error:
                    _set_failure(listing, error)
                    image_count = 0
                    print(f"{listing_label}: {error}", flush=True)
                else:
                    listing["gallery_urls"] = gallery_urls
                    listing["gallery_count"] = len(gallery_urls)
                    listing.pop("gallery_error", None)
                    image_count = listing["gallery_count"]
                    if image_count == 0:
                        print(f"{listing_label}: 0 image hashes found", flush=True)

            processed_this_run += 1
            if processed_this_run % SAVE_INTERVAL == 0:
                _save_results(payload)
                print(f"Saved progress after {processed_this_run} listings", flush=True)
            if processed_this_run % 10 == 0:
                elapsed = time.monotonic() - started_at
                average = elapsed / processed_this_run
                completed = already_done + processed_this_run
                print(
                    f"[{completed}/{len(listings)}] {image_count} images found | avg {average:.1f}s/listing",
                    flush=True,
                )
            if processed_this_run < len(remaining):
                await asyncio.sleep(random.uniform(3, 5))
    except KeyboardInterrupt:
        print("Interrupted; saving current gallery progress.", flush=True)
    except Exception as exc:
        print(f"Gallery scraper setup failed: {exc}", flush=True)
    finally:
        runtime_seconds = time.monotonic() - started_at
        if payload is not None:
            _save_results(payload)
        if homepage is not None:
            try:
                await homepage.close()
            except Exception:
                pass
        if created_context is not None:
            try:
                await created_context.close()
            except Exception:
                pass
        if playwright is not None:
            await playwright.stop()
        if payload is not None:
            _print_summary(payload, runtime_seconds)


if __name__ == "__main__":
    asyncio.run(main())
