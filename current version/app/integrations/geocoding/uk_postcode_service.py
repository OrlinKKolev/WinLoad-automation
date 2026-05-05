from __future__ import annotations

from typing import NamedTuple, Tuple

import requests

POSTCODES_IO_BASE = "https://api.postcodes.io/postcodes"


class SiteGeoResult(NamedTuple):
    easting: int
    northing: int
    postcode: str
    country: str
    district: str


def get_lat_lon_from_postcode(postcode: str) -> Tuple[float, float]:
    """Get (latitude, longitude) from a UK postcode using postcodes.io."""
    url = f"{POSTCODES_IO_BASE}/{postcode.replace(' ', '')}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != 200 or not data.get("result"):
        raise ValueError(f"Postcode not found: {postcode}")
    res = data["result"]
    return float(res["latitude"]), float(res["longitude"])


def get_site_geo(lat: float, lon: float, radius_m: int = 500) -> SiteGeoResult:
    """Return postcode, OS easting/northing, country and district for coordinates."""
    params = {"lon": lon, "lat": lat, "radius": radius_m, "limit": 1}
    r = requests.get(POSTCODES_IO_BASE, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != 200 or not data.get("result"):
        raise ValueError(
            f"No postcode found within {radius_m}m of ({lat}, {lon}). "
            "Try increasing radius_m up to 2000."
        )
    result = data["result"][0]
    return SiteGeoResult(
        easting=int(result["eastings"]),
        northing=int(result["northings"]),
        postcode=result["postcode"],
        country=result["country"],
        district=result.get("ttwa") or result.get("admin_district", ""),
    )