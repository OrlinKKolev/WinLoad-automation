"""Orchestrate ce(z) retrieval for ALL schemes in wind_example.xlsx.

Workflow per row:
1. Resolve coordinates (from lat/lon columns, or from postcode if absent).
2. get_site_geo() → postcode, OS easting/northing, city, country (one API call).
3. get_distance_to_sea_km() and get_elevation_m().
4. Build scheme JSON.
5. Website: load JSON → OS datum → vbmap → Calculate → ce(z), vb0.
6. Write all results back to Excel.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.utils import parse_number
from tools.geo.geo_location_toolset import (
    get_lat_lon_from_postcode,
    get_site_geo,
    get_distance_to_sea_km,
    get_elevation_m,
)
from tools.wind_json_builder import build_and_save_scheme_json
from tools.web.web_automation_toolset import load_json_calculate_get_cez

INPUT_EXCEL  = "schemes_input.xlsx"
OUTPUT_EXCEL = "schemes_output.xlsx"
TEMP_DIR     = project_root / "data" / "temp"
REPORTS_DIR  = project_root / "data" / "reports"

# OUTPUT_COLS = [
#     "ce_z", "vb0", "DistanceToSea_km", "Elevation_m",
#     "City", "Country", "Postcode", "OS_Easting", "OS_Northing",
# ]



def process_scheme(df: pd.DataFrame, idx: int) -> dict:
    row = df.iloc[idx]
    scheme_id = row["SchemeID"]
    postcode  = str(row.get("Postcode") or "").strip()
    lat       = row.get("Latitude")
    lon       = row.get("Longitude")

    # ── 1. Resolve coordinates ─────────────────────────────────────────────
    if pd.notna(lat) and pd.notna(lon):
        lat = float(f"{parse_number(lat):.6f}")
        lon = float(f"{parse_number(lon):.6f}")
        if not (-90.0 <= lat <= 90.0):
            raise ValueError(f"[{scheme_id}] Latitude {lat} out of range")
        if not (-180.0 <= lon <= 180.0):
            raise ValueError(f"[{scheme_id}] Longitude {lon} out of range")
        df.at[idx, "Latitude"]  = lat
        df.at[idx, "Longitude"] = lon
    elif postcode:
        lat, lon = get_lat_lon_from_postcode(postcode)
        df.at[idx, "Latitude"]  = lat
        df.at[idx, "Longitude"] = lon
    else:
        raise ValueError(f"[{scheme_id}] No coordinates and no postcode.")

    # ── 2. Site geo: postcode, OS grid, city, country (one API call) ───────
    geo = get_site_geo(lat, lon)
    print(f"[{scheme_id}] {geo.postcode} | {geo.district}, {geo.country} | E={geo.easting} N={geo.northing}")

    # ── 3. Distance to sea and elevation ───────────────────────────────────
    dist_sea  = get_distance_to_sea_km(lat, lon)
    elevation = get_elevation_m(lat, lon)
    print(f"[{scheme_id}] Distance to sea: {dist_sea} km | Elevation: {elevation} m")

    # ── 4. Build scheme JSON ───────────────────────────────────────────────
    json_path = build_and_save_scheme_json({
        "scheme_id":        scheme_id,
        "H":                parse_number(row["H"]),
        "DistanceToSea_km": dist_sea,
        "Elevation_m":      elevation,
        "Project":          str(scheme_id),
    }, TEMP_DIR)
    print(f"[{scheme_id}] JSON saved: {json_path}")

    # ── 5. Website automation ──────────────────────────────────────────────
    pdf_path = REPORTS_DIR / f"scheme_{scheme_id}_wind_result.pdf"
    cez, vb0 = load_json_calculate_get_cez(
        json_path=json_path,
        os_easting=geo.easting,
        os_northing=geo.northing,
        pdf_path=pdf_path,
        headless=True,
    )
    print(f"[{scheme_id}] ce(z) = {cez} | vb0 = {vb0}")

    return {
        "ce_z":             cez,
        "vb0":              vb0,
        "DistanceToSea_km": dist_sea,
        "Elevation_m":      elevation,
        "City":             geo.district,
        "Country":          geo.country,
        "Postcode":         geo.postcode,
        "OS_Easting":       geo.easting,
        "OS_Northing":      geo.northing,
    }


def main() -> None:
    input_path  = project_root / "data" / INPUT_EXCEL
    output_path = project_root / "data" / OUTPUT_EXCEL

    df = pd.read_excel(input_path, sheet_name="Schemes")
    if df.empty:
        raise RuntimeError("Schemes sheet is empty.")

    # Always rewrite SchemeID as a clean 1, 2, 3... counter
    df["SchemeID"] = range(1, len(df) + 1)
    df["SchemeID"] = df["SchemeID"].astype(int)

    STRING_COLS  = ["City", "Country", "Postcode"]
    NUMERIC_COLS = ["ce_z", "vb0", "DistanceToSea_km", "Elevation_m", "OS_Easting", "OS_Northing"]

    for col in NUMERIC_COLS:
        if col not in df.columns:
            df[col] = pd.Series(dtype="float64")
    for col in STRING_COLS:
        if col not in df.columns:
            df[col] = pd.Series(dtype="object")
        else:
            df[col] = df[col].astype("object")

    for idx in range(len(df)):
        scheme_id = df.at[idx, "SchemeID"]
        try:
            result = process_scheme(df, idx)
            for col in NUMERIC_COLS:
                df.at[idx, col] = float(result[col])
            for col in STRING_COLS:
                df.at[idx, col] = str(result[col])
        except Exception as e:
            print(f"[{scheme_id}] ERROR: {e}")
            df.at[idx, "ce_z"] = None

        # Always write to output, never touch input
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Schemes", index=False)
        print(f"[{scheme_id}] Output Excel updated.")

    print("All schemes processed.")


if __name__ == "__main__":
    main()
