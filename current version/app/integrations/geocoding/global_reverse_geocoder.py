from __future__ import annotations

import requests


def get_global_location_from_lat_lon(lat: float, lon: float) -> tuple[str, str, str]:
    """Return (city, country_code, country) from coordinates using BigDataCloud."""
    url = "https://api.bigdatacloud.net/data/reverse-geocode-client"
    params = {
        "latitude": lat,
        "longitude": lon,
        "localityLanguage": "en",
    }

    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    city = (
        data.get("city")
        or data.get("locality")
        or data.get("principalSubdivision")
        or ""
    ).strip()

    country = (data.get("countryName") or "").strip()
    country_code = (data.get("countryCode") or "").strip().upper()

    if not country_code:
        raise RuntimeError(f"Could not determine country for ({lat}, {lon})")

    return city, country_code, country