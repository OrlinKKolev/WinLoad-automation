"""Geolocation and site-parameter utilities for Wind Calc Auto.

This module centralizes all external geodata lookups:

- Coordinates (lat, lon) from UK postcodes via postcodes.io
- Nearest postcode from coordinates via postcodes.io reverse geocoding
- Distance to nearest coastline (km) from coordinates via the dist2coast_1deg grid
- Elevation (m) from coordinates via the Open-Elevation API
- OS National Grid eastings/northings from postcode via postcodes.io

All functions are pure utilities and do not depend on Excel or Playwright.
"""

from __future__ import annotations

from typing import Tuple

import requests

POSTCODES_IO_BASE = "https://api.postcodes.io/postcodes"
DIST2COAST_BASE = "https://pae-paha.pacioos.hawaii.edu/erddap/griddap/dist2coast_1deg.csv"
OPEN_ELEVATION_BASE = "https://api.open-elevation.com/api/v1/lookup"


def get_lat_lon_from_postcode(postcode: str) -> Tuple[float, float]:
    """Get (latitude, longitude) from a UK postcode using postcodes.io.

    Raises ValueError if the postcode is not found.
    """
    url = f"{POSTCODES_IO_BASE}/{postcode.replace(' ', '')}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != 200 or not data.get("result"):
        raise ValueError(f"Postcode not found: {postcode}")
    res = data["result"]
    return float(res["latitude"]), float(res["longitude"])


def get_postcode_from_lat_lon(lat: float, lon: float) -> str:
    """Get nearest UK postcode for (lat, lon) using postcodes.io reverse geocoding."""
    url = POSTCODES_IO_BASE
    params = {"lon": lon, "lat": lat}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != 200 or not data.get("result"):
        raise ValueError(f"No postcode found for coordinates {lat}, {lon}")
    return data["result"][0]["postcode"]


def get_distance_to_sea_km(lat: float, lon: float) -> float:
    """Distance to nearest coastline (km) from coordinates using dist2coast_1deg.

    Dataset: "Distance to Nearest Coastline: 0.01-Degree Grid" (global, ~0.01°),
    variable "dist" in km. Negative values are over land, positive over ocean,
    so this function returns abs(dist).
    """
    url = f"{DIST2COAST_BASE}?dist[({lat})][({lon})]"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    lines = r.text.strip().splitlines()
    if len(lines) < 3:
        raise RuntimeError(f"Unexpected dist2coast response for {lat},{lon}: {r.text!r}")
    # Third line is like: '51.5,-0.02,-19'
    parts = lines[2].split(",")
    if len(parts) < 3:
        raise RuntimeError(f"Unexpected dist2coast row for {lat},{lon}: {lines[2]!r}")
    dist = float(parts[2])
    return abs(dist)


def get_elevation_m(lat: float, lon: float) -> float:
    """Get elevation (m) from coordinates using the Open-Elevation API."""
    params = {"locations": f"{lat},{lon}"}
    r = requests.get(OPEN_ELEVATION_BASE, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])
    if not results:
        raise RuntimeError(f"No elevation result for {lat}, {lon}")
    return float(results[0]["elevation"])


def get_os_grid_from_postcode(postcode: str) -> Tuple[int, int]:
    """Get OS National Grid eastings/northings (meters) from UK postcode.

    Uses postcodes.io and returns (eastings, northings) as integers.
    """
    url = f"{POSTCODES_IO_BASE}/{postcode.replace(' ', '')}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != 200 or not data.get("result"):
        raise ValueError(f"Postcode not found: {postcode}")
    res = data["result"]
    east = int(res["eastings"])
    north = int(res["northings"])
    return east, north
