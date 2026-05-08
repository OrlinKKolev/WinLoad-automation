"""Distance to sea via Doogal's DistanceToSea page."""

from __future__ import annotations

import re
import threading

from playwright.sync_api import sync_playwright

DOOGAL_DISTANCE_URL = "https://www.doogal.co.uk/DistanceToSea"


def _dismiss_cookie_overlay(page) -> None:
    """Best-effort cookie consent dismissal. Never raises."""
    # Try clicking known reject/disagree buttons
    for selector in [
        "text=DISAGREE",
        "text=Disagree",
        "text=REJECT ALL",
        "text=Reject All",
        "text=Reject all",
        "button[mode='secondary']",
        ".qc-cmp2-summary-buttons button:first-child",
    ]:
        try:
            page.wait_for_selector(selector, timeout=1500)
            page.click(selector, timeout=2000)
            page.wait_for_timeout(500)
            return
        except Exception:
            continue

    # Fallback: nuke all known overlay containers from the DOM
    try:
        page.evaluate("""
            [
                '#qc-cmp2-container',
                '.qc-cmp2-container',
                '.qc-cmp-cleanslate',
                '[data-nosnippet]',
            ].forEach(sel => {
                document.querySelectorAll(sel).forEach(el => el.remove());
            });
        """)
        page.wait_for_timeout(300)
    except Exception:
        pass


def _click_calculate(page) -> None:
    """Click the Calculate button, bypassing any remaining overlay."""
    selector = "input[value='Calculate']"

    # First attempt: force=True bypasses pointer-event interception
    try:
        page.click(selector, force=True, timeout=5000)
        return
    except Exception:
        pass

    # Second attempt: trigger via JavaScript onclick directly
    try:
        page.evaluate("""
            const btn = document.querySelector("input[value='Calculate']");
            if (btn) btn.click();
        """)
        return
    except Exception:
        pass

    # Final attempt: dispatch a real MouseEvent via JS
    page.evaluate("""
        const btn = document.querySelector("input[value='Calculate']");
        if (btn) {
            btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
        }
    """)


def _run_doogal(lat: float, lon: float, headless: bool, result: list) -> None:
    coord_line = f"{lat:.6f},{lon:.6f}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        page.goto(DOOGAL_DISTANCE_URL, wait_until="domcontentloaded", timeout=60000)

        # Give page JS a moment to render
        page.wait_for_timeout(1500)

        # Dismiss cookie overlay
        _dismiss_cookie_overlay(page)

        # Fill coordinates
        page.fill("textarea", coord_line)
        page.wait_for_timeout(300)

        # Nuke overlay again right before click as final safety net
        try:
            page.evaluate("""
                [
                    '#qc-cmp2-container',
                    '.qc-cmp2-container',
                    '.qc-cmp-cleanslate',
                    '[data-nosnippet]',
                ].forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => el.remove());
                });
            """)
        except Exception:
            pass

        # Click Calculate
        _click_calculate(page)

        # Wait for results table to appear — more reliable than matching coord string
        try:
            page.wait_for_selector("table tbody tr", timeout=20000)
        except Exception:
            # Wait for results table to appear — avoids fragile coordinate string matching
            page.wait_for_selector("table tbody tr td", timeout=20000)

        body_text = page.inner_text("body")
        browser.close()

    m = re.search(
        r"-?\d+\.?\d*,\s*-?\d+\.?\d*\s+(\d+\.?\d*)\s+(\d+\.?\d*)",
        body_text,
    )
    if not m:
        raise RuntimeError(f"Could not find distance result for {lat},{lon}")
    dist_km = float(m.group(2))
    print(f"Distance to sea: {float(m.group(1))} miles / {dist_km} km")
    result.append(dist_km)


def get_distance_to_sea_km(lat: float, lon: float, headless: bool = True) -> float:
    """Distance to sea (km) for (lat, lon) via Doogal."""
    result: list[float] = []
    exc_holder: list[Exception] = []

    def target():
        try:
            _run_doogal(lat, lon, headless, result)
        except Exception as e:
            exc_holder.append(e)

    t = threading.Thread(target=target)
    t.start()
    t.join()

    if exc_holder:
        raise exc_holder[0]
    return result[0]