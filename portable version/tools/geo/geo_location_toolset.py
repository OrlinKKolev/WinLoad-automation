"""Geolocation and site-parameter utilities for Wind Calc Auto.

Public functions:
- get_lat_lon_from_postcode(postcode)  : postcode → (lat, lon)
- get_site_geo(lat, lon)               : lat/lon → SiteGeoResult (postcode, OS grid, city, country)
- get_distance_to_sea_km(lat, lon)     : lat/lon → km to coast via Doogal
- get_elevation_m(lat, lon)            : lat/lon → elevation in metres
"""

from __future__ import annotations

from typing import NamedTuple, Tuple

import requests

from tools.web.doogal_distance_tool import get_distance_to_sea_km_doogal

POSTCODES_IO_BASE    = "https://api.postcodes.io/postcodes"
ELEVATION_API_BASE   = "https://www.elevation-api.eu/v1/elevation"


class SiteGeoResult(NamedTuple):
    easting:  int
    northing: int
    postcode: str   # full postcode e.g. "LS12 1AB"
    country:  str   # "England", "Scotland", "Wales"
    district: str   # admin_district e.g. "Leeds"


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
    """Single postcodes.io call returning full postcode, OS easting/northing,
    country and district for the given coordinates.
    radius_m: 1–2000m. Default 500m.
    """
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
        district=result.get("ttwa") or result.get("admin_district", ""),  # ttwa preferred, fallback to admin_district
    )


def get_distance_to_sea_km(lat: float, lon: float) -> float:
    """Distance to nearest coastline (km) via Doogal."""
    return get_distance_to_sea_km_doogal(lat, lon)


def get_elevation_m(lat: float, lon: float) -> float:
    """Elevation (m) from coordinates using elevation-api.eu (SRTM, no key required)."""
    r = requests.get(f"{ELEVATION_API_BASE}/{lat}/{lon}", timeout=10)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, (int, float)):
        return float(data)
    if isinstance(data, dict) and "elevation" in data:
        return float(data["elevation"])
    raise RuntimeError(f"Unexpected elevation response for ({lat}, {lon}): {data}")
