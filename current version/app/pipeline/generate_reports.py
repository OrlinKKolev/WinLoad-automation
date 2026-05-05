from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

from app.integrations.excel.excel_pdf_export import export_active_sheet_page1_to_pdf
from app.integrations.excel.wind_check_template import populate_wind_check_template


DATA_ROOT = project_root / "data"
SOURCE_EXCEL = DATA_ROOT / "schemes_output.xlsx"
TEMPLATE_EXCEL = DATA_ROOT / "STxxxx_Wind load check.xlsx"
REPORTS_DIR = DATA_ROOT / "reports"

CELL_MAP = [
    ("T11", "vb0", None),
    ("T18", "H", None),
    ("T19", "H", None),
    ("T20", "B", None),
    ("T21", "L", None),
    ("P25", "Elevation_m", None),
    ("P26", "ce_z", None),
    ("P27", None, 1.0),
]

def main() -> None:
    if not SOURCE_EXCEL.exists():
        raise FileNotFoundError(f"Source Excel not found: {SOURCE_EXCEL}")
    if not TEMPLATE_EXCEL.exists():
        raise FileNotFoundError(f"Template Excel not found: {TEMPLATE_EXCEL}")

    df = pd.read_excel(SOURCE_EXCEL, sheet_name="Schemes")
    if df.empty:
        raise RuntimeError("Schemes sheet is empty — nothing to process.")

    required = ["SchemeID", "H", "B", "L", "Elevation_m", "ce_z"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"Source Excel is missing columns: {missing}")

    errors = 0
    for _, row in df.iterrows():
        scheme_id = row["SchemeID"]

        if str(row.get("ce_z", "")).upper() in ("ERROR", "NONE", "NAN", ""):
            print(f"[{scheme_id}] SKIPPED — ce_z is not a valid result")
            continue

        print(f"[{scheme_id}] Populating wind check Excel...")
        output_path = REPORTS_DIR / f"scheme_{scheme_id}_Wind_load_check.xlsx"
        pdf_path = REPORTS_DIR / f"scheme_{scheme_id}_Wind_load_check.pdf"

        try:
            populate_wind_check_template(row.to_dict(), TEMPLATE_EXCEL, output_path)
            export_active_sheet_page1_to_pdf(output_path, pdf_path)
            print(f"[{scheme_id}] Done.")
        except Exception as e:
            print(f"[{scheme_id}] ERROR: {e}")
            errors += 1

    print(f"\\nAll schemes processed. {errors} error(s).")


if __name__ == "__main__":
    main()