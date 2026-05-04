"""Distance to sea via Doogal's DistanceToSea page."""

from __future__ import annotations

import re
import threading

from playwright.sync_api import sync_playwright

DOOGAL_DISTANCE_URL = "https://www.doogal.co.uk/DistanceToSea"


def _dismiss_cookie_popup(page) -> None:
    try:
        page.wait_for_selector("text=DISAGREE", timeout=1500)
        page.click("text=DISAGREE")
    except Exception:
        pass


def _run_doogal(lat: float, lon: float, headless: bool, result: list) -> None:
    coord_line = f"{lat:.6f},{lon:.6f}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(DOOGAL_DISTANCE_URL, wait_until="networkidle")
        _dismiss_cookie_popup(page)
        page.fill("textarea", coord_line)
        page.click("input[value='Calculate']")
        page.wait_for_function(
            f"() => document.body.innerText.includes('{coord_line}')",
            timeout=15000,
        )
        body_text = page.inner_text("body")
        browser.close()

    m = re.search(r"-?\d+\.?\d*,\s*-?\d+\.?\d*\s+(\d+\.?\d*)\s+(\d+\.?\d*)", body_text)
    if not m:
        raise RuntimeError(f"Could not find distance result for {lat},{lon}")
    dist_km = float(m.group(2))
    print(f"Distance to sea: {float(m.group(1))} miles / {dist_km} km")
    result.append(dist_km)


def get_distance_to_sea_km_doogal(lat: float, lon: float, headless: bool = True) -> float:
    """Distance to sea (km) for (lat, lon) via Doogal. Runs in a separate thread
    to avoid asyncio event loop conflicts with Playwright.
    """
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
