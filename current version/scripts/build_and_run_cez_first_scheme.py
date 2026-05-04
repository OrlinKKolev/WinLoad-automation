"""Build JSON for first scheme, load into EurocodeApplied, fetch ce(z),
and write it back into the Excel workbook.

This script:
 1. Reads the first data row from Schemes sheet.
 2. Ensures coordinates exist (using postcode if needed).
 3. Computes distance to sea and elevation (if not already present).
 4. Builds a JSON config matching the EurocodeApplied SAVE/LOAD format.
 5. Stores it under data/temp/scheme_1.json.
 6. Uses Playwright automation to load the JSON, run CALCULATE, and
    extract ce(z).
 7. Writes ce(z) back into the same row in Excel.

Usage:
    python build_and_run_cez_first_scheme.py

Requirements:
    pip install pandas openpyxl requests playwright
    playwright install
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from tools.geo.geo_location_toolset import (
    get_lat_lon_from_postcode,
    get_postcode_from_lat_lon,
    get_distance_to_sea_km,
    get_elevation_m,
)
from tools.web.web_automation_toolset import load_wind_json_and_get_cez

# Default basic wind velocity if not specified elsewhere (m/s)
VBMAP_DEFAULT = 21.57

# Fixed token copied from a working JSON export; the site appears to
# accept it when loading configs via the UI.
REQUEST_VERIFICATION_TOKEN = (
    "CfDJ8GyiMZkFCtpIndt9zBOb5jkiTMSFlOvb6r2j-lxIW1jk6-E2nv8uib2BOg59SfaL3ReQMeYWUjPt6OzoDbp2gPsEnSB7bfRXYmI65ltVk2FDbt4VBtxKb8mGObSIDDNq6bvL_ERfRD5U_WbnzFvjbak"
)

EXCEL_NAME = "wind_example.xlsx"


def build_json_from_row(row: pd.Series) -> dict:
    """Build a JSON dict for the EurocodeApplied calculator from one Excel row.

    Mapping (for now):
      - vbmap: fixed VBMAP_DEFAULT (can later be replaced by OS-datum value).
      - Altitude: Elevation_m from Excel (or 0 if missing).
      - dShore: DistanceToSea_km from Excel (or 0 if missing).
      - z: H (height) from Excel.
      - Other factors use sensible defaults from the sample JSON.
    """
    scheme_id = row.get("SchemeID", "")

    altitude = float(row.get("Elevation_m") or 0.0)
    d_shore = float(row.get("DistanceToSea_km") or 0.0)
    z = float(row.get("H") or 0.0)

    data = {
        "Calculation.CalculationMethod": "0",
        "Calculation.vbmap": f"{VBMAP_DEFAULT:.2f}",
        "Calculation.Altitude": f"{altitude:.0f}",
        "Calculation.DirectionalFactor": "25",  # from example JSON
        "Calculation.dShore": f"{d_shore:.1f}",
        "Calculation.dTown": "0",
        "Calculation.z": f"{z:.3f}",
        "Calculation.hdis": "0",
        "Calculation.c0_z": "1",
        "Calculation.cseason": "1",
        "__RequestVerificationToken": REQUEST_VERIFICATION_TOKEN,
        "Calculation.Project": str(scheme_id),
        "Calculation.Subject": "",
        "Calculation.Designer": "",
        "Calculation.Date": "",
    }
    return data


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent

    excel_path = project_root / "data" / EXCEL_NAME
    temp_dir = project_root / "data" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(excel_path, sheet_name="Schemes")

    if df.empty:
        raise RuntimeError("Schemes sheet is empty; no rows to process.")

    # Work on the first data row (index 0)
    idx = 0
    row = df.iloc[idx].copy()

    scheme_id = row["SchemeID"]
    postcode = str(row.get("Postcode") or "").strip()
    lat = row.get("Latitude")
    lon = row.get("Longitude")

    # Ensure coordinates exist (coordinates take precedence)
    if pd.notna(lat) and pd.notna(lon):
        lat = float(lat)
        lon = float(lon)
    elif postcode:
        lat, lon = get_lat_lon_from_postcode(postcode)
        df.at[idx, "Latitude"] = lat
        df.at[idx, "Longitude"] = lon
        row["Latitude"] = lat
        row["Longitude"] = lon
    else:
        raise ValueError(
            f"Row {idx}: no coordinates and no postcode for SchemeID {scheme_id}"
        )

    # Optional: ensure postcode exists for this location
    if not postcode:
        try:
            postcode = get_postcode_from_lat_lon(lat, lon)
            df.at[idx, "Postcode"] = postcode
            row["Postcode"] = postcode
        except Exception:
            pass

    # Compute / refresh geodata if needed
    if pd.isna(row.get("DistanceToSea_km")):
        dist_sea = get_distance_to_sea_km(lat, lon)
        df.at[idx, "DistanceToSea_km"] = dist_sea
        row["DistanceToSea_km"] = dist_sea
    if pd.isna(row.get("Elevation_m")):
        elevation = get_elevation_m(lat, lon)
        df.at[idx, "Elevation_m"] = elevation
        row["Elevation_m"] = elevation

    # Build JSON dict and write to file
    json_data = build_json_from_row(row)
    json_path = temp_dir / "scheme_1.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False)

    print(f"Built JSON for SchemeID={scheme_id} -> {json_path}")

    # Call web automation to load JSON and obtain ce(z)
    cez = load_wind_json_and_get_cez(json_path, headless=True)
    print(f"ce(z) from EurocodeApplied = {cez}")

    # Write ce(z) back into Excel for this row
    if "ce_z" not in df.columns:
        df["ce_z"] = None
    df.at[idx, "ce_z"] = cez

    with pd.ExcelWriter(
        excel_path, mode="a", if_sheet_exists="replace", engine="openpyxl"
    ) as writer:
        df.to_excel(writer, sheet_name="Schemes", index=False)

    print("Excel updated with ce(z) for first scheme.")


if __name__ == "__main__":
    main()
