"""Web automation helpers for EurocodeApplied wind calculator.

Public functions:

- extract_cez_from_text(text)         : parse ce(z) from page text
- save_result_as_pdf(page, pdf_path)  : save page as PDF
- get_vbmap_from_os_datum(page, east, north)
                                      : click #vbmap, enter OS datum via dialogs,
                                        return the vb,map value the site computed
- load_json_calculate_get_cez(...)    : full sequence:
    1. open page
    2. load JSON (vbmap=99.99 placeholder)
    3. overwrite vbmap via OS datum dialogs
    4. click CALCULATE
    5. extract ce(z) from page text
    6. save result JSON (overwrite input) and read back vbmap = vb0
    7. save result as PDF
    8. close browser
    returns (cez, vb0)

Nothing in this module touches Excel or geolocation APIs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright, Page

from tools.utils import pause_for_inspection

EUROCODE_URL = (
    "https://eurocodeapplied.com/design/en1991/"
    "wind-peak-velocity-pressure-ireland-and-uk"
)


# ── Parsing ───────────────────────────────────────────────────────────────────

def extract_cez_from_text(text: str) -> float:
    """Extract ce(z) from the plain text body of the result page."""
    pattern = r"ce\(z\)\s*=\s*([0-9]+(?:\.[0-9]+)?)"
    matches = re.findall(pattern, text)
    if not matches:
        raise ValueError("Could not find ce(z) pattern in page text")
    return float(matches[-1])


# ── PDF export ────────────────────────────────────────────────────────────────

def save_result_as_pdf(page: Page, pdf_path: Path | str) -> None:
    """Save the current page as PDF using Playwright's built-in PDF export."""
    pdf_path = Path(pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    page.pdf(path=str(pdf_path), format="A4")
    print(f"PDF saved: {pdf_path}")


# ── vb,map via OS datum dialogs ───────────────────────────────────────────────

def get_vbmap_from_os_datum(
    page: Page,
    os_easting: int,
    os_northing: int,
) -> float:
    """Click the #vbmap button, enter OS datum coordinates via the prompt
    dialog, accept the result alert, and return the vb,map value.
    """
    vbmap_value: list[float] = []

    def handle_dialog(dialog):
        if dialog.type == "prompt":
            dialog.accept(f"{os_easting}, {os_northing}")
        else:
            m = re.search(r"wind velocity\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*m/s", dialog.message)
            if m:
                vbmap_value.append(float(m.group(1)))
            dialog.accept()

    page.on("dialog", handle_dialog)
    page.click("#vbmap")
    page.wait_for_timeout(2000)
    page.remove_listener("dialog", handle_dialog)

    if not vbmap_value:
        raise RuntimeError(
            f"Could not parse vb,map from OS datum dialogs for "
            f"easting={os_easting}, northing={os_northing}"
        )
    return vbmap_value[0]


# ── Full sequence ─────────────────────────────────────────────────────────────

def load_json_calculate_get_cez(
    json_path: Path,
    os_easting: int,
    os_northing: int,
    pdf_path: Path | str,
    headless: bool = True,
) -> tuple[float, float]:
    """Run the full calculation sequence and return (cez, vb0)."""
    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    p = sync_playwright().start()
    browser = p.chromium.launch(headless=headless)
    page = browser.new_page()
    page.goto(EUROCODE_URL, wait_until="networkidle")

    # Step 1: load JSON (vbmap=99.99 placeholder)
    page.click("button.load")
    page.set_input_files("input[type='file']", str(json_path))
    page.click("#calculation-load")
    page.wait_for_timeout(2000)

    # Step 2: overwrite vbmap with real value from OS datum
    vbmap = get_vbmap_from_os_datum(page, os_easting, os_northing)
    print(f"vb,map from OS datum: {vbmap} m/s")

    # Step 3: calculate
    page.click("#calculation-calculate")
    page.wait_for_timeout(3000)

    # Step 4: extract ce(z) from plain text
    text = page.inner_text("body")
    cez = extract_cez_from_text(text)
    print(f"ce(z) = {cez}")

    # Step 5: save result JSON — overwrites input JSON, then read back vb0
    with page.expect_download() as dl_info:
        page.click("button.save")
    dl_info.value.save_as(str(json_path))

    with open(json_path, encoding="utf-8") as f:
        saved = json.load(f)
    vb0 = float(saved["Calculation.vbmap"])
    print(f"vb0 = {vb0} m/s")

    # Step 6: save result as PDF
    save_result_as_pdf(page, pdf_path)

    # Step 7: close browser
    browser.close()
    p.stop()

    return cez, vb0
