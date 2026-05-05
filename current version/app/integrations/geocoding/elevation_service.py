from __future__ import annotations

import requests

ELEVATION_API_BASE = "https://www.elevation-api.eu/v1/elevation"


def get_elevation_m(lat: float, lon: float) -> float:
    """Elevation (m) from coordinates using elevation-api.eu."""
    r = requests.get(f"{ELEVATION_API_BASE}/{lat}/{lon}", timeout=10)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, (int, float)):
        return float(data)
    if isinstance(data, dict) and "elevation" in data:
        return float(data["elevation"])
    raise RuntimeError(f"Unexpected elevation response for ({lat}, {lon}): {data}")