from __future__ import annotations

from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from cdp_pool import ensure_initialized, pool
from config import Settings
from local_store import ContextStore


CLOUDFLARE_MARKERS = (
    "cloudflare",
    "security verification",
    "verify you are human",
    "checking your browser",
    "just a moment",
    "cf-ray",
    "ray id:",
    "performance and security by",
)
NAVIGATION_TIMEOUT_MS = 45_000
POST_LOAD_WAIT_MS = 2_000
MAX_TEXT_CHARS = 5_000


def _detect_cloudflare(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in CLOUDFLARE_MARKERS)


def _compact_text(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    compact_lines = [line for line in lines if line.strip()]
    return "\n".join(compact_lines).strip()


def _truncate_text(text: str) -> str:
    if len(text) <= MAX_TEXT_CHARS:
        return text
    marker = "\n[truncated]"
    return text[: MAX_TEXT_CHARS - len(marker)].rstrip() + marker


def _format_content(text: str, links: list[str]) -> str:
    text_portion = _compact_text(text)[:4000].strip()
    links_portion = "\n".join(links) if links else "No links found"
    content = f"{text_portion}\n\n## Links Found:\n{links_portion}" if text_portion else f"## Links Found:\n{links_portion}"
    return _truncate_text(content)


async def _browse_with_cdp(settings: Settings, url: str, cdp_port: int | None = None) -> dict[str, Any]:
    playwright: Playwright | None = None
    browser: Browser | None = None
    context: BrowserContext | None = None
    page: Page | None = None
    created_context = False
    ensure_initialized()
    acquired_here = cdp_port is None
    if acquired_here:
        acquired = pool.acquire()
        if acquired.get("status") != "acquired":
            raise RuntimeError(str(acquired.get("error") or "No CDP pool slot is available"))
        resolved_port = int(acquired["port"])
    else:
        resolved_port = cdp_port
        pool.endpoint_for(resolved_port)
    cdp_endpoint = f"http://localhost:{resolved_port}"

    try:
        del settings
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(cdp_endpoint)
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = await browser.new_context()
            created_context = True
        page = await context.new_page()
        page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
        await page.goto(url, timeout=NAVIGATION_TIMEOUT_MS, wait_until="domcontentloaded")
        await page.wait_for_timeout(POST_LOAD_WAIT_MS)

        title = (await page.title()).strip()
        if _detect_cloudflare(title):
            return {
                "ok": False,
                "url": url,
                "title": title,
                "cloudflare_challenge": True,
                "error": "Cloudflare challenge detected",
            }

        text = _compact_text(await page.inner_text("body"))
        links = await page.evaluate(
            """() => {
                const priorityPattern = /dealer|wholesale|distributor|reseller|retailer|stockist|become a dealer|find a dealer|contact|support|where to buy/i;
                const seen = new Set();
                const links = Array.from(document.querySelectorAll('a[href]'))
                    .map(a => ({text: a.textContent.trim(), href: a.href}))
                    .filter(l => l.text.length > 1 && !l.href.startsWith('javascript:'))
                    .filter(l => {
                        const key = `${l.text}::${l.href}`;
                        if (seen.has(key)) return false;
                        seen.add(key);
                        return true;
                    })
                    .sort((a, b) => {
                        const aPriority = priorityPattern.test(`${a.text} ${a.href}`) ? 1 : 0;
                        const bPriority = priorityPattern.test(`${b.text} ${b.href}`) ? 1 : 0;
                        return bPriority - aPriority;
                    })
                    .slice(0, 30);
                return links.map(l => l.text + ': ' + l.href);
            }"""
        )

        if not text:
            snapshot = await page.locator("body").aria_snapshot()
            text = _compact_text(snapshot)

        if not text:
            return {
                "ok": False,
                "url": url,
                "title": title,
                "cloudflare_challenge": False,
                "error": "Page did not contain readable content",
            }

        content = _format_content(text, links)
        if not content:
            return {
                "ok": False,
                "url": url,
                "title": title,
                "cloudflare_challenge": False,
                "error": "Page content did not contain readable text",
            }

        if _detect_cloudflare(content):
            return {
                "ok": False,
                "url": url,
                "title": title,
                "cloudflare_challenge": True,
                "error": "Cloudflare challenge detected",
            }

        return {
            "ok": True,
            "url": url,
            "title": title,
            "cloudflare_challenge": False,
            "text": content,
            "token_estimate": max(1, len(content) // 4),
            "source": "chrome_cdp_accessibility",
            "cdp_port": resolved_port,
            "cdp_endpoint": cdp_endpoint,
        }
    finally:
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
        if acquired_here:
            pool.release(resolved_port)


async def handle_browse_page(
    *,
    settings: Settings,
    store: ContextStore,
    url: str,
    task: str = "Extract wholesale, dealer, distributor, contact, Faire, and Amazon marketplace restriction evidence.",
    cdp_port: int | None = None,
    session_id: str = "",
    brand_name: str = "",
    ai_id: str = "",
) -> dict[str, Any]:
    del task
    session_id = store.ensure_session(session_id, brand_name or url, ai_id)
    turn = store.increment_turn(session_id, brand_name or url, ai_id)
    resolved_port: int | None = None
    resolved_endpoint = ""

    try:
        payload = await _browse_with_cdp(settings, url, cdp_port)
        resolved_port = int(payload.get("cdp_port") or 0) or None
        resolved_endpoint = str(payload.get("cdp_endpoint") or "")
        text = payload.get("text") or payload.get("error") or ""
        summary = (
            "Cloudflare challenge detected"
            if payload.get("cloudflare_challenge")
            else f"Browsed {url}; {len(text)} characters returned."
            if payload.get("ok")
            else f"browse_page failed for {url}: {payload.get('error', 'unknown error')}"
        )
        result_id = store.add_tool_result(
            session_id=session_id,
            turn=turn,
            tool_name="browse_page",
            query=url,
            result_summary=summary,
            full_result=payload,
        )
        if payload.get("cloudflare_challenge"):
            return {
                "ok": False,
                "session_id": session_id,
                "turn": turn,
                "stored_result_id": result_id,
                "url": url,
                "cloudflare_challenge": True,
                "summary": summary,
                "action": "Do not spend more turns on this page unless the brand has no other sourcing evidence.",
            }
        if not payload.get("ok"):
            return {
                "ok": False,
                "session_id": session_id,
                "turn": turn,
                "stored_result_id": result_id,
                "url": url,
                "error": str(payload.get("error") or "CDP browse failed"),
                "cloudflare_challenge": False,
            }
        return {
            "ok": True,
            "session_id": session_id,
            "turn": turn,
            "stored_result_id": result_id,
            "url": url,
            "title": payload.get("title", ""),
            "cloudflare_challenge": False,
            "text": str(payload.get("text") or ""),
            "token_estimate": int(payload.get("token_estimate") or 0),
        }
    except Exception as exc:
        summary = f"browse_page failed for {url}: {exc}"
        result_id = store.add_tool_result(
            session_id=session_id,
            turn=turn,
            tool_name="browse_page",
            query=url,
            result_summary=summary,
            full_result={"error": str(exc), "cdp_port": resolved_port, "cdp_endpoint": resolved_endpoint},
        )
        return {
            "ok": False,
            "session_id": session_id,
            "turn": turn,
            "stored_result_id": result_id,
            "url": url,
            "error": str(exc),
            "cloudflare_challenge": False,
        }
