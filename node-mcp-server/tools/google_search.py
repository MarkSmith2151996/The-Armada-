from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import quote_plus, urlparse

from playwright.async_api import Browser, BrowserContext, Page, Playwright, TimeoutError, async_playwright

from cdp_pool import ensure_initialized, pool
from config import Settings
from local_store import ContextStore


GOOGLE_TIMEOUT_MS = 15_000
MAX_RESULTS = 10


def _is_google_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host == "google.com" or host.endswith(".google.com")


async def _google_results(query: str, cdp_port: int | None) -> tuple[list[dict[str, str]], int]:
    ensure_initialized()
    acquired_here = cdp_port is None
    resolved_port: int | None = None
    if acquired_here:
        acquired = pool.acquire()
        if acquired.get("status") != "acquired":
            raise RuntimeError(str(acquired.get("error") or "No CDP pool slot is available"))
        resolved_port = int(acquired["port"])
    else:
        resolved_port = cdp_port
        pool.endpoint_for(resolved_port)

    playwright: Playwright | None = None
    browser: Browser | None = None
    context: BrowserContext | None = None
    page: Page | None = None
    created_context = False
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(f"http://localhost:{resolved_port}")
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = await browser.new_context()
            created_context = True
        page = await context.new_page()
        page.set_default_navigation_timeout(GOOGLE_TIMEOUT_MS)
        await page.goto(f"https://www.google.com/search?q={quote_plus(query)}", wait_until="domcontentloaded")

        body_text = (await page.locator("body").inner_text()).lower()
        if "unusual traffic" in body_text or "recaptcha" in body_text or "captcha" in body_text:
            raise RuntimeError("CAPTCHA detected")
        await page.locator("#search, #rso").wait_for(timeout=GOOGLE_TIMEOUT_MS)

        results: list[dict[str, str]] = []
        links = page.locator("#search a:has(h3)")
        for index in range(await links.count()):
            link = links.nth(index)
            href = await link.get_attribute("href") or ""
            title = (await link.locator("h3").inner_text()).strip()
            if not title or not href or _is_google_url(href):
                continue

            block = link.locator("xpath=ancestor::div[@data-hveid][1]")
            block_text = (await block.inner_text()).strip()
            if "sponsored" in block_text.lower():
                continue
            snippet = await block.locator(".VwiC3b, .aCOpRe, [data-sncf]").all_inner_texts()
            results.append(
                {
                    "title": title[:180],
                    "url": href,
                    "snippet": " ".join(text.strip() for text in snippet if text.strip())[:500],
                }
            )
            if len(results) == MAX_RESULTS:
                break
        return results, resolved_port
    finally:
        if page is not None:
            await page.close()
        if created_context and context is not None:
            await context.close()
        if browser is not None:
            await browser._impl_obj._connection.stop_async()
        elif playwright is not None:
            await playwright.stop()
        if acquired_here and resolved_port is not None:
            pool.release(resolved_port)


def handle_google_search(
    *,
    settings: Settings,
    store: ContextStore,
    query: str,
    cdp_port: int | None = None,
) -> dict[str, Any]:
    del settings
    search_query = query.strip()
    session_id = store.ensure_session("", search_query or "google_search", "")
    turn = store.increment_turn(session_id, search_query or "google_search", "")
    if not search_query:
        return {"ok": False, "session_id": session_id, "turn": turn, "error": "query is required"}

    try:
        results, resolved_port = asyncio.run(_google_results(search_query, cdp_port))
        summary = f"{len(results)} Google organic results for {search_query}; returned top {len(results)}."
        result_id = store.add_tool_result(
            session_id=session_id,
            turn=turn,
            tool_name="google_search",
            query=search_query,
            result_summary=summary,
            full_result={"results": results, "cdp_port": resolved_port},
        )
        return {
            "ok": True,
            "session_id": session_id,
            "turn": turn,
            "stored_result_id": result_id,
            "query": search_query,
            "summary": summary,
            "top_results": results,
        }
    except TimeoutError:
        error = "Google search timed out after 15 seconds"
    except Exception as exc:
        error = str(exc)

    result_id = store.add_tool_result(
        session_id=session_id,
        turn=turn,
        tool_name="google_search",
        query=search_query,
        result_summary=f"google_search failed for {search_query}: {error}",
        full_result={"error": error, "cdp_port": cdp_port},
    )
    return {
        "ok": False,
        "session_id": session_id,
        "turn": turn,
        "stored_result_id": result_id,
        "query": search_query,
        "error": error,
    }
