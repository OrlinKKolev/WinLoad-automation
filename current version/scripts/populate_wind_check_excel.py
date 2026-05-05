"""
Read completed results from wind_example.xlsx (Schemes sheet) and for each
row copy the parameters into the STxxxx_Wind load check.xlsx template,
then save a filled copy per scheme into the same reports folder as the PDFs.

Cell mapping (STxxxx template):
    T18  ← H   (building height, used twice — T18 and T19)
    T19  ← H
    T20  ← B   (building width)
    T21  ← L   (building length)
    P25  ← Elevation_m
    P26  ← ce_z
    P27  ← 1.0 (fixed value)

Run AFTER run_first_scheme_cez.py has finished populating wind_example.xlsx.

Usage:
    python scripts/populate_wind_check_excel.py
"""

from __future__ import annotations

import sys
from pathlib import Path
import shutil
import openpyxl

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


from tools.utils import parse_number
from tools.project_root import PROJECT_ROOT
# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_ROOT = PROJECT_ROOT.parent / "data" 

SOURCE_EXCEL   = DATA_ROOT / "schemes_output.xlsx"
TEMPLATE_EXCEL = DATA_ROOT / "STxxxx_Wind load check.xlsx"
REPORTS_DIR    = DATA_ROOT / "reports"

# ── Cell mapping ──────────────────────────────────────────────────────────────
# Each entry: (cell_address, column_name_in_source, fixed_value_or_None)
CELL_MAP = [
    ("T11", "vb0",         None),
    ("T18", "H",           None),
    ("T19", "H",           None),
    ("T20", "B",           None),
    ("T21", "L",           None),
    ("P25", "Elevation_m", None),
    ("P26", "ce_z",        None),
    ("P27", None,          1.0 ),   # fixed value
]


def populate_scheme(row: dict, template_path: Path, output_path: Path) -> None:
    """Fill the template with one scheme's data and save to output_path.

    Steps:
    1) Copy template file to output_path (preserves images, formatting, protection).
    2) Open the copied file.
    3) Temporarily unprotect the active sheet.
    4) Write mapped values into the configured cells.
    5) Re‑enable protection with the same settings as the template.
    """

    # 1) Ensure folder exists and copy template as a real file copy
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template_path, output_path)

    # 2) Open the copied workbook
    wb = openpyxl.load_workbook(output_path)
    ws = wb.active  # assumes data is on the first/active sheet

    # 3) Temporarily unprotect the sheet (password and options stay on the object)
    ws.protection.sheet = False  # just turns the flag off, does not clear password[web:61]

    # 4) Write values to cells according to CELL_MAP
    for cell_addr, col_name, fixed_value in CELL_MAP:
        if fixed_value is not None:
            ws[cell_addr] = fixed_value
        else:
            raw = row.get(col_name)
            if raw is None:
                raise ValueError(f"Column '{col_name}' not found in source row")
            ws[cell_addr] = parse_number(raw)

    # 5) Re‑enable protection with the same parameters as template
    ws.protection.sheet = False   # password + allowed actions remain as in template[web:61]

    wb.save(str(output_path))
    print(f"  Saved: {output_path}")

def export_active_sheet_page1_to_pdf(excel_path: Path, pdf_path: Path) -> None:
    import win32com.client

    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    excel.ScreenUpdating = False

    wb = None
    try:
        wb = excel.Workbooks.Open(str(excel_path.resolve()))
        ws = wb.ActiveSheet

        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        ws.ExportAsFixedFormat(
            Type=0,
            Filename=str(pdf_path.resolve()),
            Quality=0,
            IncludeDocProperties=True,
            IgnorePrintAreas=False,
            From=1,
            To=1,
            OpenAfterPublish=False,
        )
    finally:
        if wb is not None:
            wb.Close(SaveChanges=False)
        excel.Quit()
def main() -> None:
    import pandas as pd

    # ── Read completed source data ─────────────────────────────────────────
    if not SOURCE_EXCEL.exists():
        raise FileNotFoundError(f"Source Excel not found: {SOURCE_EXCEL}")
    if not TEMPLATE_EXCEL.exists():
        raise FileNotFoundError(f"Template Excel not found: {TEMPLATE_EXCEL}")

    df = pd.read_excel(SOURCE_EXCEL, sheet_name="Schemes")
    if df.empty:
        raise RuntimeError("Schemes sheet is empty — nothing to process.")

    # ── Validate required columns exist ───────────────────────────────────
    required = ["SchemeID", "H", "B", "L", "Elevation_m", "ce_z"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"Source Excel is missing columns: {missing}")

    # ── Process each row ──────────────────────────────────────────────────
    errors = 0
    for idx, row in df.iterrows():
        scheme_id = row["SchemeID"]

        # Skip rows that were not successfully processed
        if str(row.get("ce_z", "")).upper() in ("ERROR", "NONE", "NAN", ""):
            print(f"[{scheme_id}] SKIPPED — ce_z is not a valid result")
            continue

        print(f"[{scheme_id}] Populating wind check Excel...")
        output_path = REPORTS_DIR / f"scheme_{scheme_id}_Wind_load_check.xlsx"
        pdf_path = REPORTS_DIR / f"scheme_{scheme_id}_Wind_load_check.pdf"

        try:
            populate_scheme(row.to_dict(), TEMPLATE_EXCEL, output_path)
            export_active_sheet_page1_to_pdf(output_path, pdf_path)
            print(f"[{scheme_id}] Done.")
        except Exception as e:
            print(f"[{scheme_id}] ERROR: {e}")
            errors += 1

    print(f"\nAll schemes processed. {errors} error(s).")


if __name__ == "__main__":
    main()

