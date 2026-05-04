"""
Demo: open EurocodeApplied UK & Irish NA wind calculator,
click the vb,map button, enter OS datum coordinates, and
accept the two dialogs (prompt + result alert).

Usage:
    python vbmap_osdatum_demo.py

Requirements:
    pip install playwright
    playwright install
"""

from pathlib import Path  # not strictly needed, but handy if you extend this
from playwright.sync_api import sync_playwright

EUROCODE_URL = (
    "https://eurocodeapplied.com/design/en1991/"
    "wind-peak-velocity-pressure-ireland-and-uk"
)

# Example OS datum coordinates (X Eastings, Y Northings) in meters
OS_EASTING = 532500
OS_NORTHING = 180500


def main() -> None:
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)  # visible browser
    page = browser.new_page()
    page.goto(EUROCODE_URL, wait_until="networkidle")

    # Dialog handler: first dialog is a prompt for "X, Y", second is an alert with the result
    def handle_dialog(dialog):
        text = dialog.message
        print(f"Dialog type={dialog.type}, message={text!r}")
        if dialog.type == "prompt":
            # Fill OS datum as comma-separated X, Y
            coord_text = f"{OS_EASTING}, {OS_NORTHING}"
            dialog.accept(coord_text)
            print(f"Entered OS datum: {coord_text}")
        else:
            # For the result alert, just click OK
            dialog.accept()
            print("Result dialog accepted")

    page.on("dialog", handle_dialog)

    # 1) Click the vb,map button: <button id="vbmap"><i>v</i><sub>b,map</sub></button>
    page.click("#vbmap")

    # 2) Give the page a bit of time for the dialogs and for vb,map to be transferred
    page.wait_for_timeout(3000)

    print("vb,map OS datum demo complete.")
    print("Browser is still open; check that vb,map has been populated, then close it manually.")

    # Do NOT close browser automatically so you can review the page
    # When you are done, you can close the window and then Ctrl+C this script
    # or you can uncomment the lines below:
    # browser.close()
    # p.stop()


if __name__ == "__main__":
    main()
