"""Web automation helpers for EurocodeApplied wind calculator.

This module encapsulates Playwright-based interactions with the
EurocodeApplied UK & Irish National Annex wind peak velocity
pressure calculator:

- vbmap_osdatum_demo: populate vb,map from OS datum coordinates via dialogs.
- extract_cez_from_html: parse ce(z) from the explanatory text.
- load_wind_json_and_get_cez: load a JSON config, run calculation, return ce(z).

These functions do not touch Excel and are callable from higher-level scripts.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Tuple

from playwright.sync_api import sync_playwright, Page

EUROCODE_URL = (
    "https://eurocodeapplied.com/design/en1991/"
    "wind-peak-velocity-pressure-ireland-and-uk"
)


def extract_cez_from_html(html: str) -> float:
    """Extract ce(z) from the explanatory paragraph in the result HTML.

    Looks for a pattern like:
        ... as ce(z) = 2.012.
    and returns the numeric value.
    """
    pattern = r"ce\(.*?\)\s*=\s*([0-9]+(?:\.[0-9]+)?)"
    m = re.search(pattern, html)
    if not m:
        raise ValueError("Could not find ce(z) pattern in page HTML")
    return float(m.group(1))


def _open_calculator_page(headless: bool = True) -> Tuple[object, object, Page]:
    """Internal helper to start Playwright, open browser and page on calculator URL.

    Returns (playwright, browser, page).
    Caller is responsible for closing browser and stopping playwright.
    """
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=headless)
    page = browser.new_page()
    page.goto(EUROCODE_URL, wait_until="networkidle")
    return p, browser, page


def vbmap_osdatum_demo(os_easting: int, os_northing: int, headless: bool = False) -> None:
    """Click vb,map, enter OS datum (X, Y) via dialogs, and accept result.

    This is mainly for debugging / manual confirmation; it leaves
    the browser open if headless=False.
    """
    p, browser, page = _open_calculator_page(headless=headless)

    def handle_dialog(dialog):
        text = dialog.message
        print(f"Dialog type={dialog.type}, message={text!r}")
        if dialog.type == "prompt":
            coord_text = f"{os_easting}, {os_northing}"
            dialog.accept(coord_text)
            print(f"Entered OS datum: {coord_text}")
        else:
            dialog.accept()
            print("Result dialog accepted")

    page.on("dialog", handle_dialog)

    page.click("#vbmap")
    page.wait_for_timeout(3000)

    if headless:
        browser.close()
        p.stop()
    else:
        print("vb,map OS datum demo complete. Close the browser when finished.")


def load_wind_json_and_get_cez(json_path: Path, headless: bool = True) -> float:
    """Load a JSON config into the calculator, run CALCULATE, and return ce(z).

    The browser is closed automatically when headless=True. For debugging,
    call with headless=False and close the browser manually.
    """
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    p, browser, page = _open_calculator_page(headless=headless)

    # Click LOAD button
    page.click("button.load")

    # Attach JSON file to underlying <input type='file'>
    page.set_input_files("input[type='file']", str(json_path))

    # Click OK after loading JSON
    page.click("#calculation-load")

    page.wait_for_timeout(2000)

    # Click CALCULATE
    page.click("#calculation-calculate")

    page.wait_for_timeout(3000)

    html = page.content()
    cez = extract_cez_from_html(html)

    if headless:
        browser.close()
        p.stop()

    return cez
