from __future__ import annotations


def process_eu_scheme(
    *,
    city_name: str,
    country_code: str,
    country_name: str,
) -> dict:
    """Return placeholder result for non-UK schemes.

    EU/non-UK wind calculation is not implemented yet, so for now we only
    return route-identifying and location fields and leave UK-only numeric
    outputs empty.
    """
    return {
        "ce_z": None,
        "vb0": None,
        "DistanceToSea_km": None,
        "Elevation_m": None,
        "City": city_name,
        "CountryCode": country_code,
        "Country": country_name,
        "Postcode": "",
        "OS_Easting": None,
        "OS_Northing": None,
        "isUK": False,
    }