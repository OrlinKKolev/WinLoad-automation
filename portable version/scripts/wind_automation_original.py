"""Wind data automation example (coordinates + postcode fallback).

Logic per row in Schemes sheet:

1. If Latitude and Longitude are present, use them.
2. Else, if Postcode is present, use postcodes.io to get coordinates
   and write them back into Latitude/Longitude.
3. If Postcode is missing but coordinates exist, reverse-geocode
   nearest postcode via postcodes.io and write it back.
4. Use postcode with Doogal to get distance to sea (km).
5. Use coordinates with Open-Elevation to get elevation (m).
6. Write results into WindData sheet.

Dependencies (install once):
    pip install pandas openpyxl requests beautifulsoup4

"""

from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

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


def get_distance_to_sea_km(postcode: str) -> float:
    """Scrape Doogal postcode page for "Distance to sea" (km)."""
    url = f"https://www.doogal.co.uk/ShowMap?postcode={postcode.replace(' ', '+')}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    for tr in soup.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if not cells:
            continue
        if any("Distance to sea" in c.get_text(strip=True) for c in cells):
            for td in tr.find_all("td"):
                txt = td.get_text(strip=True)
                if not txt:
                    continue
                num = ""
                for ch in txt:
                    if ch.isdigit() or ch == ".":
                        num += ch
                    else:
                        break
                if num:
                    return float(num)

    raise RuntimeError(f"Could not find Distance to sea for postcode {postcode}")


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

    results = []
    for idx, row in df.iterrows():
        scheme_id = row["SchemeID"]
        postcode = str(row.get("Postcode") or "").strip()

        lat = row.get("Latitude")
        lon = row.get("Longitude")

        # 1) Determine coordinates (source of truth)
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

        # 2) Ensure we have a postcode for Doogal distance
        if not postcode:
            postcode = get_postcode_from_lat_lon(lat, lon)
            df.at[idx, "Postcode"] = postcode

        # 3) Use postcode for distance to sea; coords for elevation
        dist_sea = get_distance_to_sea_km(postcode)
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

        results.append(
            {
                "SchemeID": scheme_id,
                "DistanceToSea_km": dist_sea,
                "Elevation_m": elevation,
                "ce_z": ce_z,
            }
        )

    res_df = pd.DataFrame(results)

    with pd.ExcelWriter(excel_path, mode="a", if_sheet_exists="replace", engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Schemes", index=False)
        res_df.to_excel(writer, sheet_name="WindData", index=False)


if __name__ == "__main__":
    main()
