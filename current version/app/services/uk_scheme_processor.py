from __future__ import annotations

from app.integrations.coastal.distance_to_sea_service import get_distance_to_sea_km
from app.integrations.geocoding.elevation_service import get_elevation_m
from app.integrations.geocoding.uk_postcode_service import get_site_geo
from app.integrations.eurocode.uk_json_builder import build_and_save_scheme_json
from app.integrations.eurocode.eurocode_applied_client import load_json_calculate_get_cez


def process_uk_scheme(
    *,
    scheme_id,
    row,
    lat: float,
    lon: float,
    country_code: str,
    temp_dir,
    reports_dir,
    parse_number,
) -> dict:
    """Run the existing working UK route and return output fields."""

    geo = get_site_geo(lat, lon)
    print(
        f"[{scheme_id}] {geo.postcode} | {geo.district}, {geo.country} | "
        f"E={geo.easting} N={geo.northing}"
    )

    dist_sea = get_distance_to_sea_km(lat, lon)
    elevation = get_elevation_m(lat, lon)
    print(f"[{scheme_id}] Distance to sea: {dist_sea} km | Elevation: {elevation} m")

    json_path = build_and_save_scheme_json(
        {
            "scheme_id": scheme_id,
            "H": parse_number(row["H"]),
            "DistanceToSea_km": dist_sea,
            "Elevation_m": elevation,
            "Project": str(scheme_id),
        },
        temp_dir,
    )
    print(f"[{scheme_id}] JSON saved: {json_path}")

    pdf_path = reports_dir / f"scheme_{scheme_id}_EurocodeApplied_Result.pdf"
    cez, vb0 = load_json_calculate_get_cez(
        json_path=json_path,
        os_easting=geo.easting,
        os_northing=geo.northing,
        pdf_path=pdf_path,
        headless=True,
    )
    print(f"[{scheme_id}] ce(z) = {cez} | vb0 = {vb0}")

    return {
        "ce_z": cez,
        "vb0": vb0,
        "DistanceToSea_km": dist_sea,
        "Elevation_m": elevation,
        "City": geo.district,
        "CountryCode": country_code,
        "Country": geo.country,
        "Postcode": geo.postcode,
        "OS_Easting": geo.easting,
        "OS_Northing": geo.northing,
        "isUK": True,
    }