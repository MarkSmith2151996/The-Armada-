#!/usr/bin/env python3
"""Mac-based Keepa Prescreen Batch Runner.

Connects to Postgres via SSH tunnel (localhost:5433) and uses Playwright with
persistent Chromium profile to download Keepa Product Finder CSVs.

Usage:
    python3 run_prescreen_batch_mac.py --batch-ids "2546,2547,2550"
    python3 run_prescreen_batch_mac.py --max-batches 5 --max-parallel 3
"""

import asyncio
import csv
import json
import logging
import os
import re
import shutil
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2 import pool
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

log = logging.getLogger("prescreen-mac")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

PG_CONFIG = {
    "host": os.environ.get("FBA_PG_HOST", "localhost"),
    "port": int(os.environ.get("FBA_PG_PORT", 5433)),
    "dbname": os.environ.get("FBA_PG_DB", "hive"),
    "user": os.environ.get("FBA_PG_USER", "fba_writer"),
    "password": os.environ.get("FBA_PG_PASS", "fba_pipeline_2026"),
    "options": "-c search_path=fba,public",
}

PROFILE_DIR = str(Path.home() / "keepa-browser-profile")
EXPORT_BASE = Path(os.environ.get("KEEPA_EXPORT_DIR", str(Path.home() / "keepa_exports")))
BATCH_EXPORT_DIR = EXPORT_BASE / "batches"

_pool_obj = None

def _get_pool():
    global _pool_obj
    if _pool_obj is None:
        _pool_obj = pool.ThreadedConnectionPool(1, 10, **PG_CONFIG)
    return _pool_obj

def query(sql, params=None):
    conn = _get_pool().getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        _get_pool().putconn(conn)

def execute(sql, params=None):
    conn = _get_pool().getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _get_pool().putconn(conn)

def load_batches(batch_ids=None, max_batches=0):
    if batch_ids:
        rows = query(
            """SELECT id, batch_number, batch_url,
                      filter_params->>'manufacturer_url' AS manufacturer_url
               FROM prescreen_batch
               WHERE id = ANY(%s) AND status = 'queued'
               ORDER BY batch_number, id""",
            (batch_ids,),
        )
    else:
        sql = """SELECT id, batch_number, batch_url,
                        filter_params->>'manufacturer_url' AS manufacturer_url
                 FROM prescreen_batch
                 WHERE status = 'queued'
                   AND id BETWEEN 2546 AND 2766
                 ORDER BY batch_number, id"""
        params = ()
        if max_batches > 0:
            sql += " LIMIT %s"
            params = (max_batches,)
        rows = query(sql, params or None)
    return rows

def mark_downloaded(batch_id, primary_filename, primary_result_count, primary_csv_rows,
                    brand_filename=None, brand_result_count=0, brand_csv_rows=0,
                    manufacturer_filename=None, manufacturer_result_count=0, manufacturer_csv_rows=0):
    execute(
        """UPDATE prescreen_batch
           SET status = 'downloaded',
               csv_path = %s,
               result_count = %s,
               csv_rows = %s,
               filter_params = COALESCE(filter_params, '{}'::jsonb) || jsonb_build_object(
                   'brand_csv_path', %s,
                   'brand_result_count', %s,
                   'brand_csv_rows', %s,
                   'manufacturer_csv_path', %s,
                   'manufacturer_result_count', %s,
                   'manufacturer_csv_rows', %s
               ),
               error_detail = NULL
           WHERE id = %s""",
        (primary_filename, primary_result_count, primary_csv_rows,
         brand_filename, brand_result_count, brand_csv_rows,
         manufacturer_filename, manufacturer_result_count, manufacturer_csv_rows,
         batch_id),
    )
    execute(
        """UPDATE brand
           SET status = 'downloaded', downloaded_at = now(), csv_path = %s,
               pipeline_error = NULL, updated_at = now()
           WHERE batch_id = %s""",
        (primary_filename, batch_id),
    )

def mark_zero_results(batch_id):
    execute(
        """UPDATE prescreen_batch
           SET status = 'zero_results', csv_path = NULL, result_count = 0, csv_rows = 0,
               filter_params = COALESCE(filter_params, '{}'::jsonb) || jsonb_build_object(
                   'brand_csv_path', NULL, 'brand_result_count', 0, 'brand_csv_rows', 0,
                   'manufacturer_csv_path', NULL, 'manufacturer_result_count', 0, 'manufacturer_csv_rows', 0
               ),
               error_detail = NULL
           WHERE id = %s""",
        (batch_id,),
    )

def mark_error(batch_id, error_detail):
    execute(
        """UPDATE prescreen_batch
           SET status = 'error', error_detail = %s
           WHERE id = %s""",
        (str(error_detail)[:2000], batch_id),
    )

def count_csv_data_rows(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        return sum(1 for _ in reader)

# --- Playwright Keepa Automaton ---

SEL_PAGINATION_SUMMARY = ".ag-paging-row-summary-panel"
SEL_EXPORT_BUTTON = "span.tool__export"
SEL_EXPORT_MODAL_BUTTON = "button:has-text('EXPORT')"
SEL_GRID_SCAFFOLD = ".ag-root-wrapper"
SEL_FILTER_SUBMIT = "#filterSubmit"
SEL_PAGE_SIZE = "span.tool__row"

JS_FINDER_HAS_ZERO = (
    "() => {"
    " const t = (document.querySelector('.ag-paging-row-summary-panel')||{}).innerText||'';"
    " const b = document.body.innerText || '';"
    " return /No results found/i.test(b)"
    "     || /No products found/i.test(b)"
    "     || /\\b0\\s+results\\b/i.test(b)"
    "     || /0\\s+to\\s+0\\s+of\\s+0/i.test(t);"
    "}"
)

JS_GRID_HAS_ROWS = (
    "() => Array.from(document.querySelectorAll('.ag-center-cols-container .ag-row'))"
    ".some(row => (row.innerText || row.textContent || '').trim().length > 20)"
)

JS_SUMMARY_HAS_TOTAL = (
    "() => /\\bof\\s+([\\d,]+|more)\\b/.test("
    "(document.querySelector('.ag-paging-row-summary-panel')||{}).innerText||'')"
)

JS_RESULT_TEXT = (
    "() => {"
    " const el = document.querySelector('.ag-paging-row-summary-panel, .finder-result-count');"
    " return el ? (el.innerText || el.textContent || '').trim() : 'not_found';"
    "}"
)

async def wait_for_results_or_zero(page, timeout_ms=20000):
    row_wait = asyncio.create_task(page.wait_for_function(JS_GRID_HAS_ROWS, timeout=timeout_ms))
    zero_wait = asyncio.create_task(page.wait_for_function(JS_FINDER_HAS_ZERO, timeout=timeout_ms))
    done, pending = await asyncio.wait({row_wait, zero_wait}, return_when=asyncio.FIRST_COMPLETED)
    winner = done.pop()
    winner_is_zero = winner is zero_wait
    for task in pending:
        if not task.done():
            task.cancel()
    for task in pending:
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass
    try:
        await winner
    except (asyncio.CancelledError, Exception):
        pass
    return "zero_results" if winner_is_zero else "rows"

async def dismiss_keepa_popup(page):
    for sel in ("#shareChartOverlay-close", "#popup3 .close", "#popup3 [aria-label='close']"):
        try:
            loc = page.locator(sel)
            if await loc.is_visible(timeout=1500):
                await loc.click(timeout=2000)
                await page.wait_for_timeout(400)
                return
        except Exception:
            continue
    try:
        visible = await page.evaluate(
            "() => { const p = document.getElementById('popup3');"
            " if (!p) return false;"
            " const s = window.getComputedStyle(p);"
            " return s.display !== 'none' && s.visibility !== 'hidden' && p.offsetHeight > 0; }"
        )
        if visible:
            await page.evaluate(
                "() => { const p = document.getElementById('popup3');"
                " if (p) p.style.setProperty('display','none','important'); }"
            )
            await page.wait_for_timeout(300)
    except Exception:
        pass

async def set_page_size_5000(page):
    try:
        page_size_el = await page.wait_for_selector(SEL_PAGE_SIZE, timeout=10000)
    except Exception:
        ready = await page.evaluate(
            """() => {
                const body = document.body.innerText || '';
                if (/No results found/i.test(body)) return true;
                const t = (document.querySelector('.ag-paging-row-summary-panel')||{}).innerText||'';
                if (/0\\s+to\\s+0\\s+of\\s+0/i.test(t)) return true;
                const m = t.match(/(\\d[\\d,]*)\\s+to\\s+(\\d[\\d,]*)\\s+of\\s+(\\d[\\d,]*)/);
                if (!m) return false;
                const upper = parseInt(m[2].replace(/,/g,''),10);
                const total = parseInt(m[3].replace(/,/g,''),10);
                return total <= 5000 || upper >= 500;
            }"""
        )
        if ready:
            return
        raise
    await page_size_el.evaluate("el => el.click()")
    await page.wait_for_timeout(500)
    clicked = await page.evaluate(
        """() => {
            const candidates = Array.from(document.querySelectorAll('.mdc-menu .mdc-list-item, .mdc-menu li, li, [role="menuitem"], [role="option"]'));
            const option = candidates.find(el => (el.innerText || el.textContent || '').trim().replace(',', '') === '5000');
            if (!option) return false;
            option.click();
            return true;
        }"""
    )
    if clicked:
        return
    changed = await page.evaluate(
        """() => {
            const select = document.querySelector('.ag-paging-page-size select');
            if (!select) return false;
            select.value = '5000';
            select.dispatchEvent(new Event('change', { bubbles: true }));
            return true;
        }"""
    )
    if changed:
        return
    has_rows = await page.evaluate(
        """() => {
            if (/No results found/i.test(document.body.innerText||'')) return true;
            const t = (document.querySelector('.ag-paging-row-summary-panel')||{}).innerText||'';
            if (/0\\s+to\\s+0\\s+of\\s+0/i.test(t)) return true;
            return /\\d[\\d,]*\\s+to\\s+\\d[\\d,]*\\s+of\\s+(\\d[\\d,]*|more)/.test(t);
        }"""
    )
    if has_rows:
        return
    raise RuntimeError("could not find 5000-row option")

async def open_export_modal(page):
    export_el = await page.wait_for_selector(SEL_EXPORT_BUTTON, state="visible", timeout=30000)
    await page.evaluate(
        """() => {
            const toolbar = document.getElementById('grid-tools-finder');
            if (toolbar) {
                toolbar.style.setProperty('position', 'relative', 'important');
                toolbar.style.setProperty('z-index', '2147483647', 'important');
                toolbar.style.setProperty('pointer-events', 'auto', 'important');
            }
        }"""
    )
    await export_el.evaluate(
        """el => {
            el.click();
            el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true, view: window }));
            el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true, view: window }));
            el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
        }"""
    )
    try:
        await page.wait_for_selector("text=Export Data", timeout=3000)
        return
    except Exception:
        pass
    await page.locator(SEL_EXPORT_BUTTON).first.click(force=True, timeout=10000)
    await page.wait_for_selector("text=Export Data", timeout=15000)

def unique_download_path(output_dir, suggested):
    stem = Path(suggested).stem
    suffix = Path(suggested).suffix or ".csv"
    stamp = time.strftime("%H-%M-%S")
    millis = int((time.time() % 1) * 1000)
    out_path = output_dir / f"{stem}-{stamp}-{millis:03d}{suffix}"
    counter = 1
    while out_path.exists():
        out_path = output_dir / f"{stem}-{stamp}-{millis:03d}-{counter}{suffix}"
        counter += 1
    return out_path

async def download_one_url(page, url, output_dir, suffix):
    started = time.time()
    log.info("Downloading: %s -> %s", suffix, output_dir)
    try:
        await page.goto("about:blank")
        await page.goto(url, wait_until="domcontentloaded")
    except Exception as exc:
        return {"status": "error", "reason": f"navigation_failed: {exc}", "duration_sec": round(time.time() - started, 2), "suffix": suffix}

    try:
        await page.wait_for_selector(SEL_GRID_SCAFFOLD, state="attached", timeout=20000)
    except Exception as exc:
        return {"status": "error", "reason": f"grid_never_rendered: {exc}", "duration_sec": round(time.time() - started, 2), "suffix": suffix}

    try:
        await page.wait_for_function(JS_SUMMARY_HAS_TOTAL, timeout=15000)
    except Exception:
        try:
            await page.wait_for_function(
                "() => { const b = document.querySelector('#filterSubmit'); return b && !b.disabled && b.offsetParent !== null; }",
                timeout=30000,
            )
            await page.click(SEL_FILTER_SUBMIT)
            await page.wait_for_function(JS_SUMMARY_HAS_TOTAL, timeout=90000)
        except Exception:
            return {"status": "error", "reason": "never_got_results_summary", "duration_sec": round(time.time() - started, 2), "suffix": suffix}

    await dismiss_keepa_popup(page)

    await page.evaluate(
        """() => {
            const c = document.querySelector('div.data-container.asin');
            if (c) { c.style.setProperty('display','block','important'); c.style.setProperty('opacity','1','important'); }
        }"""
    )
    await page.wait_for_timeout(400)

    try:
        finder_state = await wait_for_results_or_zero(page)
    except Exception as exc:
        return {"status": "error", "reason": f"result_state_failed: {exc}", "duration_sec": round(time.time() - started, 2), "suffix": suffix}

    if finder_state == "zero_results":
        return {"status": "zero_results", "result_count": 0, "csv_rows": 0, "duration_sec": round(time.time() - started, 2), "suffix": suffix}

    try:
        await set_page_size_5000(page)
    except Exception as exc:
        return {"status": "error", "reason": f"page_size_failed: {exc}", "duration_sec": round(time.time() - started, 2), "suffix": suffix}

    await page.wait_for_function(
        """() => {
            const t = (document.querySelector('.ag-paging-row-summary-panel')||{}).innerText||'';
            const m = t.match(/1 to ([\\d,]+) of ([\\d,]+|more)/);
            if (!m) return false;
            const upper = parseInt(m[1].replace(/,/g,''),10);
            if (m[2] === 'more') return upper >= 500;
            const total = parseInt(m[2].replace(/,/g,''),10);
            return upper >= 500 || upper === total;
        }""",
        timeout=180000,
    )

    summary_text = await page.evaluate(JS_RESULT_TEXT)

    if await page.evaluate(JS_FINDER_HAS_ZERO):
        return {"status": "zero_results", "result_count": 0, "csv_rows": 0, "duration_sec": round(time.time() - started, 2), "suffix": suffix}

    try:
        await page.wait_for_function(JS_GRID_HAS_ROWS, timeout=60000)
    except Exception:
        if await page.evaluate(JS_FINDER_HAS_ZERO):
            return {"status": "zero_results", "result_count": 0, "csv_rows": 0, "duration_sec": round(time.time() - started, 2), "suffix": suffix}
        return {"status": "error", "reason": "grid_rows_not_visible", "duration_sec": round(time.time() - started, 2), "suffix": suffix}

    await page.wait_for_timeout(3000)

    try:
        await open_export_modal(page)
    except Exception as exc:
        return {"status": "error", "reason": f"export_modal_failed: {exc}", "duration_sec": round(time.time() - started, 2), "suffix": suffix}

    try:
        async with page.expect_download(timeout=180000) as dl_info:
            await page.click(SEL_EXPORT_MODAL_BUTTON)
        download = await dl_info.value
    except Exception as exc:
        return {"status": "error", "reason": f"download_never_completed: {exc}", "duration_sec": round(time.time() - started, 2), "suffix": suffix}

    suggested = download.suggested_filename or "KeepaExport.csv"
    out_path = unique_download_path(output_dir, suggested)
    await download.save_as(str(out_path))

    size_bytes = out_path.stat().st_size if out_path.exists() else 0
    rows_count = 0
    if summary_text:
        m = re.search(r"1 to ([\d,]+) of", summary_text)
        if m:
            rows_count = int(m.group(1).replace(",", ""))

    csv_data_rows = 0
    try:
        csv_data_rows = count_csv_data_rows(out_path)
    except Exception:
        csv_data_rows = rows_count

    await page.goto("about:blank")
    await page.wait_for_timeout(1000)

    return {
        "status": "downloaded",
        "filename": out_path.name,
        "output_path": str(out_path),
        "result_count": rows_count,
        "csv_rows": csv_data_rows,
        "size_bytes": size_bytes,
        "duration_sec": round(time.time() - started, 2),
        "suffix": suffix,
    }

async def download_batch(page, batch, semaphore):
    batch_id = batch["id"]
    batch_number = batch["batch_number"]
    batch_url = batch.get("batch_url", "")
    manufacturer_url = batch.get("manufacturer_url", "")

    batch_dir = BATCH_EXPORT_DIR / str(batch_id)
    batch_dir.mkdir(parents=True, exist_ok=True)

    result = {"batch_id": batch_id, "batch_number": batch_number, "status": "unknown"}

    try:
        async with semaphore:
            log.info("Batch %s (#%s) starting", batch_id, batch_number)

            exports = {}

            if batch_url:
                log.info("Batch %s: downloading brand URL", batch_id)
                brand_result = await download_one_url(page, batch_url, batch_dir, "brand")
                exports["brand"] = brand_result
            else:
                exports["brand"] = {"status": "skipped", "reason": "no_batch_url"}

            if manufacturer_url and manufacturer_url != batch_url:
                log.info("Batch %s: downloading manufacturer URL", batch_id)
                mfr_result = await download_one_url(page, manufacturer_url, batch_dir, "manufacturer")
                exports["manufacturer"] = mfr_result

            result["exports"] = exports

            positive = [v for v in exports.values() if v.get("status") == "downloaded"]

            if not positive:
                mark_zero_results(batch_id)
                result["status"] = "zero_results"
                log.info("Batch %s: zero results", batch_id)
                return result

            primary = _pick_primary(positive)
            mark_downloaded(
                batch_id,
                str(primary["filename"]),
                int(primary.get("result_count") or 0),
                int(primary.get("csv_rows") or 0),
                exports.get("brand", {}).get("filename"),
                int(exports.get("brand", {}).get("result_count") or 0),
                int(exports.get("brand", {}).get("csv_rows") or 0),
                exports.get("manufacturer", {}).get("filename"),
                int(exports.get("manufacturer", {}).get("result_count") or 0),
                int(exports.get("manufacturer", {}).get("csv_rows") or 0),
            )
            result["status"] = "downloaded"
            result["csv_path"] = primary["filename"]
            result["result_count"] = primary.get("result_count", 0)
            result["csv_rows"] = primary.get("csv_rows", 0)
            log.info("Batch %s: downloaded %s rows", batch_id, result["csv_rows"])

    except Exception as exc:
        detail = str(exc)
        mark_error(batch_id, detail)
        result["status"] = "error"
        result["error"] = detail
        log.error("Batch %s: error: %s", batch_id, detail)

    return result

def _pick_primary(downloaded_list):
    """Prefer the brand export if available, else the first."""
    for d in downloaded_list:
        if d.get("suffix") == "brand" and d.get("filename"):
            return d
    return downloaded_list[0]

async def run_batches(batches, max_parallel):
    semaphore = asyncio.Semaphore(max_parallel)
    results = []
    downloaded = 0
    zero_results = 0
    errors = 0

    # Launch browser with persistent profile
    async with async_playwright() as pw:
        context: BrowserContext = await pw.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=False,
            viewport={"width": 1400, "height": 900},
            accept_downloads=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        pages = context.pages
        if pages:
            page = pages[0]
        else:
            page = await context.new_page()

        # Verify Keepa login
        await page.goto("https://keepa.com", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        content = await page.content()
        logged_in = "Nutellabot01" in content or "logout" in content.lower()
        if not logged_in:
            log.warning("Not logged into Keepa - attempting login")
            await _login_to_keepa(page)
        else:
            log.info("Keepa session active")

        for batch in batches:
            result = await download_batch(page, batch, semaphore)
            results.append(result)

            if result["status"] == "downloaded":
                downloaded += 1
            elif result["status"] == "zero_results":
                zero_results += 1
            elif result["status"] == "error":
                errors += 1

        await context.close()

    return {
        "ok": True,
        "requested": len(batches),
        "downloaded": downloaded,
        "zero_results": zero_results,
        "errors": errors,
        "results": results,
    }

async def _login_to_keepa(page):
    await page.goto("https://keepa.com/#!", wait_until="domcontentloaded")
    await page.wait_for_timeout(1000)
    await page.evaluate(
        """() => {
            const overlay = document.getElementById('loginOverlay');
            if (overlay) overlay.style.display = 'block';
        }"""
    )
    await page.wait_for_timeout(500)
    await page.evaluate(
        """() => {
            const username = document.getElementById('username');
            const password = document.getElementById('password');
            if (username) {
                username.value = 'Nutellabot01';
                username.dispatchEvent(new Event('input', { bubbles: true }));
            }
            if (password) {
                password.value = 'Legos@fashion';
                password.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }"""
    )
    await page.wait_for_timeout(500)
    await page.evaluate(
        """() => {
            const submit = document.getElementById('submitLogin');
            if (submit) submit.click();
        }"""
    )
    await page.wait_for_timeout(5000)
    content = await page.content()
    if "Nutellabot01" not in content and "logout" not in content.lower():
        raise RuntimeError("Keepa login failed")
    log.info("Keepa login successful")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Mac Keepa Prescreen Batch Runner")
    parser.add_argument("--batch-ids", type=str, default="", help="Comma-separated batch IDs")
    parser.add_argument("--max-parallel", type=int, default=3, help="Max parallel downloads (default: 3)")
    parser.add_argument("--max-batches", type=int, default=0, help="Limit number of batches (0 = all)")
    args = parser.parse_args()

    BATCH_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    batch_ids = None
    if args.batch_ids:
        batch_ids = [int(x.strip()) for x in args.batch_ids.split(",") if x.strip()]

    batches = load_batches(batch_ids, args.max_batches)
    if not batches:
        log.info("No queued batches found")
        return {"ok": True, "requested": 0, "results": []}

    log.info("Loaded %d queued batches", len(batches))
    result = asyncio.run(run_batches(batches, args.max_parallel))

    log.info("Done: %d downloaded, %d zero, %d errors", result["downloaded"], result["zero_results"], result["errors"])
    return result

if __name__ == "__main__":
    sys.exit(0 if main().get("ok") else 1)
