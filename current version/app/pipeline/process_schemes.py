"""Orchestrate scheme processing for all rows in schemes_input.xlsx."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.domain.route_selector import select_route
from app.integrations.geocoding.global_reverse_geocoder import (
    get_global_location_from_lat_lon,
)
from app.integrations.geocoding.uk_postcode_service import get_lat_lon_from_postcode
from app.services.eu_scheme_processor import process_eu_scheme
from app.services.uk_scheme_processor import process_uk_scheme
from app.utils.numbers import parse_number


INPUT_EXCEL = "schemes_input.xlsx"
OUTPUT_EXCEL = "schemes_output.xlsx"
TEMP_DIR = project_root / "data" / "temp"
REPORTS_DIR = project_root / "data" / "reports"


def process_scheme(df: pd.DataFrame, idx: int) -> dict:
    row = df.iloc[idx]
    scheme_id = row["SchemeID"]
    postcode = str(row.get("Postcode") or "").strip()
    lat = row.get("Latitude")
    lon = row.get("Longitude")

    if pd.notna(lat) and pd.notna(lon):
        lat = float(f"{parse_number(lat):.6f}")
        lon = float(f"{parse_number(lon):.6f}")
        if not (-90.0 <= lat <= 90.0):
            raise ValueError(f"[{scheme_id}] Latitude {lat} out of range")
        if not (-180.0 <= lon <= 180.0):
            raise ValueError(f"[{scheme_id}] Longitude {lon} out of range")
        df.at[idx, "Latitude"] = lat
        df.at[idx, "Longitude"] = lon
    elif postcode:
        lat, lon = get_lat_lon_from_postcode(postcode)
        df.at[idx, "Latitude"] = lat
        df.at[idx, "Longitude"] = lon
    else:
        raise ValueError(f"[{scheme_id}] No coordinates and no postcode.")

    city_name, country_code, country_name = get_global_location_from_lat_lon(lat, lon)
    route = select_route(country_code)
    print(f"[{scheme_id}] Country detected: {country_name} ({country_code}) | route={route}")

    if route == "eu":
        print(f"[{scheme_id}] Non-UK location: {city_name}, {country_name}")
        return process_eu_scheme(
            city_name=city_name,
            country_code=country_code,
            country_name=country_name,
        )

    return process_uk_scheme(
        scheme_id=scheme_id,
        row=row,
        lat=lat,
        lon=lon,
        country_code=country_code,
        temp_dir=TEMP_DIR,
        reports_dir=REPORTS_DIR,
        parse_number=parse_number,
    )


def main() -> None:
    input_path = project_root / "data" / INPUT_EXCEL
    output_path = project_root / "data" / OUTPUT_EXCEL

    df = pd.read_excel(input_path, sheet_name="Schemes")
    if df.empty:
        raise RuntimeError("Schemes sheet is empty.")

    df["SchemeID"] = range(1, len(df) + 1)
    df["SchemeID"] = df["SchemeID"].astype(int)

    STRING_COLS = ["City", "CountryCode", "Country", "Postcode"]
    NUMERIC_COLS = [
        "ce_z",
        "vb0",
        "DistanceToSea_km",
        "Elevation_m",
        "OS_Easting",
        "OS_Northing",
    ]
    BOOL_COLS = ["isUK"]

    for col in NUMERIC_COLS:
        if col not in df.columns:
            df[col] = pd.Series(dtype="float64")

    for col in STRING_COLS:
        if col not in df.columns:
            df[col] = pd.Series(dtype="object")
        else:
            df[col] = df[col].astype("object")

    for col in BOOL_COLS:
        if col not in df.columns:
            df[col] = pd.Series(dtype="object")

    for idx in range(len(df)):
        scheme_id = df.at[idx, "SchemeID"]
        try:
            result = process_scheme(df, idx)

            for col in NUMERIC_COLS:
                value = result.get(col)
                df.at[idx, col] = float(value) if value is not None else None

            for col in STRING_COLS:
                value = result.get(col)
                df.at[idx, col] = str(value) if value is not None else ""

            for col in BOOL_COLS:
                df.at[idx, col] = result.get(col)

        except Exception as e:
            print(f"[{scheme_id}] ERROR: {e}")
            df.at[idx, "ce_z"] = None
            df.at[idx, "isUK"] = None

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Schemes", index=False)
        print(f"[{scheme_id}] Output Excel updated.")

    print("All schemes processed.")


if __name__ == "__main__":
    main()