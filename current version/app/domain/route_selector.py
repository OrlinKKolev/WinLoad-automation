from __future__ import annotations


def is_uk_country_code(country_code: str) -> bool:
    """Return True when the country code should follow the UK route."""
    return (country_code or "").strip().upper() == "GB"


def select_route(country_code: str) -> str:
    """Return the processing route name for a scheme."""
    return "uk" if is_uk_country_code(country_code) else "eu"