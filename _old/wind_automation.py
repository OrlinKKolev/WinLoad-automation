"""Wind data automation example.

Reads schemes from wind_example.xlsx in the same directory,
fetches distance to sea, elevation and a stub ce_z,
then writes results to the WindData sheet.

Dependencies to install (once):
    pip install pandas openpyxl requests beautifulsoup4

"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
from pathlib import Path

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


def get_distance_to_sea_km(postcode: str) -> float:
    """Scrape Doogal postcode page for 'Distance to sea' (km)."""
    url = f"https://www.doogal.co.uk/ShowMap?postcode={postcode.replace(' ', '+')}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    for tr in soup.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if not cells:
            continue
        # Check if any cell in this row contains the label text
        if any("Distance to sea" in c.get_text(strip=True) for c in cells):
            # Find the first <td> with a numeric prefix like "37.7 KMs (23.4 miles)"
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
    """Placeholder for ce(z).

    For now returns 1.0 so you can test the pipeline.
    Later you can replace this with browser automation
    against the EurocodeApplied calculator or a direct
    implementation of the UK NA formulas.
    """

    return 1.0


def main() -> None:
    here = Path(__file__).resolve().parent
    excel_path = here / EXCEL_NAME

    # Read Schemes sheet
    df = pd.read_excel(excel_path, sheet_name="Schemes")

    results = []
    for idx, row in df.iterrows():
        scheme_id = row["SchemeID"]
        postcode = str(row["Postcode"]).strip()

        lat = row.get("Latitude")
        lon = row.get("Longitude")

        # If coordinates are missing, get them from postcode and
        # write them back into the DataFrame
        if pd.isna(lat) or pd.isna(lon):
            if not postcode or postcode.lower() == "nan":
                raise ValueError(
                    f"Row {idx}: no coordinates and no valid postcode for SchemeID {scheme_id}"
                )
            lat, lon = get_lat_lon_from_postcode(postcode)
            df.at[idx, "Latitude"] = lat
            df.at[idx, "Longitude"] = lon

        # From here on we always work with coordinates
        dist_sea = get_distance_to_sea_km(postcode)  # Doogal is postcode-based
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

    # Write BOTH updated Schemes (with filled coordinates)
    # and WindData back to the same file
    with pd.ExcelWriter(
        excel_path, mode="a", if_sheet_exists="replace", engine="openpyxl"
    ) as writer:
        df.to_excel(writer, sheet_name="Schemes", index=False)
        res_df.to_excel(writer, sheet_name="WindData", index=False)



if __name__ == "__main__":
    main()
