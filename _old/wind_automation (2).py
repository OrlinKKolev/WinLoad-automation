"""Wind data automation (coordinates are the only basis for calculations).

Per row in Schemes sheet:

1. If Latitude and Longitude are present, use them.
2. Else, if Postcode is present, use postcodes.io to get coordinates
   and write them back into Latitude/Longitude.
3. If coordinates exist but Postcode is missing, reverse-geocode
   nearest postcode via postcodes.io and write it back (for info only).
4. Use coordinates with:
   - dist2coast_1deg (PacIOOS / NASA) to get distance to nearest coastline (km),
   - Open-Elevation to get elevation (m).
5. Write results into new columns in the same Schemes sheet:
   DistanceToSea_km, Elevation_m, ce_z.

Dependencies (install once):
    pip install pandas openpyxl requests
"""

from pathlib import Path

import pandas as pd
import requests

EXCEL_NAME = "wind_example.xlsx"


def get_lat_lon_from_postcode(postcode: str) -> tuple[float, float]:
    """Get latitude/longitude from UK postcode using postcodes.io."""
    url = f"https://api.postcodes.io/postcodes/{postcode.replace(' ', '')}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != 200 or not data.get("result"):
        raise ValueError(f"Postcode not found: {postcode}")
    res = data["result"]
    return float(res["latitude"]), float(res["longitude"])


def get_postcode_from_lat_lon(lat: float, lon: float) -> str:
    """Get nearest UK postcode from coordinates using postcodes.io reverse geocoding."""
    url = "https://api.postcodes.io/postcodes"
    params = {"lon": lon, "lat": lat}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != 200 or not data.get("result"):
        raise ValueError(f"No postcode found for coordinates {lat}, {lon}")
    return data["result"][0]["postcode"]


def get_distance_to_sea_km(lat: float, lon: float) -> float:
    """Distance to nearest coastline (km) from coordinates using dist2coast_1deg.

    Dataset: 'Distance to Nearest Coastline: 0.01-Degree Grid' (global, ~0.01°),
    variable 'dist' in km. Negative values are over land, positive over ocean,
    so we return abs(dist).
    """
    base = "https://pae-paha.pacioos.hawaii.edu/erddap/griddap/dist2coast_1deg.csv"
    url = f"{base}?dist[({lat})][({lon})]"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    text = r.text.strip().splitlines()
    if len(text) < 3:
        raise RuntimeError(f"Unexpected dist2coast response for {lat},{lon}: {r.text!r}")
    # Third line is like: '51.5,-0.02,-19'
    parts = text[2].split(",")
    if len(parts) < 3:
        raise RuntimeError(f"Unexpected dist2coast row for {lat},{lon}: {text[2]!r}")
    dist = float(parts[2])
    return abs(dist)


def get_elevation_m(lat: float, lon: float) -> float:
    """Get elevation (m) from coordinates using Open-Elevation API."""
    url = "https://api.open-elevation.com/api/v1/lookup"
    params = {"locations": f"{lat},{lon}"}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])
    if not results:
        raise RuntimeError(f"No elevation result for {lat}, {lon}")
    return float(results[0]["elevation"])


def get_ce_z_stub(*_, **__) -> float:
    """Placeholder for ce(z); always returns 1.0 for now."""
    return 1.0


def main() -> None:
    here = Path(__file__).resolve().parent
    excel_path = here / EXCEL_NAME

    df = pd.read_excel(excel_path, sheet_name="Schemes")

    # Ensure output columns exist so they appear at the end (after your inputs)
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
            # Fallback: postcode -> coordinates, then coordinates drive everything
            lat, lon = get_lat_lon_from_postcode(postcode)
            df.at[idx, "Latitude"] = lat
            df.at[idx, "Longitude"] = lon
        else:
            raise ValueError(
                f"Row {idx}: no coordinates and no postcode for SchemeID {scheme_id}"
            )

        # 2) Optionally ensure we have a postcode for record-keeping (not used in calcs)
        if not postcode:
            try:
                postcode = get_postcode_from_lat_lon(lat, lon)
                df.at[idx, "Postcode"] = postcode
            except Exception:
                # If reverse-geocode fails, keep going; it doesn't affect calculations.
                pass

        # 3) All calculations use coordinates only
        dist_sea = get_distance_to_sea_km(lat, lon)
        elevation = get_elevation_m(lat, lon)

        H = float(row["H"])
        B = float(row["B"])
        L = float(row["L"])

        ce_z = get_ce_z_stub(
            postcode=postcode,
            height=H,
            width=B,
            length=L,
            lat=lat,
            lon=lon,
            distance_to_sea_km=dist_sea,
            elevation_m=elevation,
        )

        df.at[idx, "DistanceToSea_km"] = dist_sea
        df.at[idx, "Elevation_m"] = elevation
        df.at[idx, "ce_z"] = ce_z

    # Overwrite Schemes sheet with updated data (including new columns)
    with pd.ExcelWriter(
        excel_path, mode="a", if_sheet_exists="replace", engine="openpyxl"
    ) as writer:
        df.to_excel(writer, sheet_name="Schemes", index=False)


if __name__ == "__main__":
    main()
