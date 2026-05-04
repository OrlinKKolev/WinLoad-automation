"""
Open the EurocodeApplied UK & Irish NA wind calculator page,
LOAD a JSON config, click OK, click CALCULATE, parse ce(z) from the HTML,
print it, and keep the browser open until you press Enter.

Usage:
    python load_wind_json.py

Requirements:
    pip install playwright
    playwright install
"""

import re
from pathlib import Path

from playwright.sync_api import sync_playwright

EUROCODE_URL = (
    "https://eurocodeapplied.com/design/en1991/"
    "wind-peak-velocity-pressure-ireland-and-uk"
)

JSON_FILENAME = "en1991_wind-peak-velocity-pressure-ireland-and-uk.json"


def extract_cez_from_html(html: str) -> float:
    """
    Extract ce(z) from the explanatory paragraph, which looks like:

        ... as <i>c</i><sub>e</sub>(<i>z</i>) = 2.012.

    Returns ce(z) as float, or raises ValueError if not found.
    """
    pattern = r"c</i><sub>e</sub>\(.*?\)\s*=\s*([0-9]+(?:\.[0-9]+)?)"
    m = re.search(pattern, html)
    if not m:
        raise ValueError("Could not find ce(z) pattern in page HTML")
    return float(m.group(1))


def main() -> None:
    here = Path(__file__).resolve().parent
    json_path = here / JSON_FILENAME
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    # Use explicit start/stop so the browser isn't auto-closed by a context manager
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)  # visible browser
    page = browser.new_page()
    page.goto(EUROCODE_URL, wait_until="networkidle")

    # 1) Click the LOAD button: <button class="load">
    page.click("button.load")

    # 2) Attach the JSON file to the underlying <input type='file'>
    page.set_input_files("input[type='file']", str(json_path))

    # 3) Click the OK button after loading JSON:
    #    <button id="calculation-load" class="ok">...</button>
    page.click("#calculation-load")

    # 4) Give the page time to populate fields
    page.wait_for_timeout(2000)

    # 5) Click the CALCULATE button (id="calculation-calculate")
    page.click("#calculation-calculate")

    # 6) Wait for the explanatory text containing ce(z) to update
    page.wait_for_timeout(3000)

    # 7) Get full page HTML and extract ce(z)
    html = page.content()
    try:
        cez = extract_cez_from_html(html)
        print(f"ce(z) = {cez}")
    except Exception as e:
        print(f"Could not extract ce(z): {e}")

    # 8) Keep browser open until user confirms
    input("Press Enter in this terminal to close the browser and exit...")

    browser.close()
    p.stop()


if __name__ == "__main__":
    main()
