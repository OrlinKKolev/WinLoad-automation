"""Main automation entry point for Wind Calc Auto.

This script reads schemes from an Excel workbook in the same directory,
uses geolocation utilities to derive site parameters, and is intended
to be extended to call web automation helpers to obtain ce(z) from the
EurocodeApplied calculator.
"""

from pathlib import Path

import pandas as pd

from tools.geo.geo_location_toolset import (
    get_lat_lon_from_postcode,
    get_postcode_from_lat_lon,
    get_distance_to_sea_km,
    get_elevation_m,
    get_os_grid_from_postcode,
)

# from tools.web.web_automation_toolset import load_wind_json_and_get_cez, vbmap_osdatum_demo

EXCEL_NAME = "wind_example.xlsx"


def main() -> None:
    here = Path(__file__).resolve().parent
    excel_path = here / "data" / EXCEL_NAME


    df = pd.read_excel(excel_path, sheet_name="Schemes")

    for col in ["DistanceToSea_km", "Elevation_m", "ce_z"]:
        if col not in df.columns:
            df[col] = None

    for idx, row in df.iterrows():
        scheme_id = row["SchemeID"]
        postcode = str(row.get("Postcode") or "").strip()

        lat = row.get("Latitude")
        lon = row.get("Longitude")

        # 1) Coordinates are the source of truth for calculations
        if pd.notna(lat) and pd.notna(lon):
            lat = float(lat)
            lon = float(lon)
        elif postcode:
            lat, lon = get_lat_lon_from_postcode(postcode)
            df.at[idx, "Latitude"] = lat
            df.at[idx, "Longitude"] = lon
        else:
            raise ValueError(
                f"Row {idx}: no coordinates and no postcode for SchemeID {scheme_id}"
            )

        # 2) Optional: ensure postcode exists for record-keeping
        if not postcode:
            try:
                postcode = get_postcode_from_lat_lon(lat, lon)
                df.at[idx, "Postcode"] = postcode
            except Exception:
                pass

        # 3) Geodata-based calculations
        dist_sea = get_distance_to_sea_km(lat, lon)
        elevation = get_elevation_m(lat, lon)

        # Placeholder: ce_z could be obtained via web_automation_toolset
        ce_z = 1.0

        df.at[idx, "DistanceToSea_km"] = dist_sea
        df.at[idx, "Elevation_m"] = elevation
        df.at[idx, "ce_z"] = ce_z

    with pd.ExcelWriter(
        excel_path, mode="a", if_sheet_exists="replace", engine="openpyxl"
    ) as writer:
        df.to_excel(writer, sheet_name="Schemes", index=False)


if __name__ == "__main__":
    main()
