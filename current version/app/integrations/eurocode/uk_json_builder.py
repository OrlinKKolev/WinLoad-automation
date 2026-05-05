"""JSON builder for the EurocodeApplied UK & Irish NA wind calculator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_REQUEST_VERIFICATION_TOKEN = (
    "CfDJ8GyiMZkFCtpIndt9zBOb5jkiTMSFlOvb6r2j-lxIW1jk6-E2nv8uib2BOg59SfaL3"
    "ReQMeYWUjPt6OzoDbp2gPsEnSB7bfRXYmI65ltVk2FDbt4VBtxKb8mGObSIDDNq6bvL_ER"
    "fRD5U_WbnzFvjbak"
)

DEFAULTS: dict[str, Any] = {
    "CalculationMethod": 0,
    "vbmap": 99.99,
    "Altitude": 0,
    "DirectionalFactor": 25,
    "dShore": 0.0,
    "dTown": 0,
    "z": 0.0,
    "hdis": 0,
    "c0_z": 1,
    "cseason": 1,
    "Project": "",
    "Subject": "",
    "Designer": "",
    "Date": "",
}


def build_and_save_scheme_json(scheme: dict[str, Any], output_dir: Path) -> Path:
    """Build a JSON config from a scheme dict and save it to output_dir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    scheme_id = str(scheme.get("scheme_id", "scheme"))

    resolved = dict(DEFAULTS)
    resolved.update(
        {
            "z": scheme.get("H", resolved["z"]),
            "Altitude": scheme.get("Elevation_m", resolved["Altitude"]),
            "dShore": scheme.get("DistanceToSea_km", resolved["dShore"]),
            "Project": scheme.get("Project", scheme_id),
        }
    )

    for key in DEFAULTS:
        if key in scheme:
            resolved[key] = scheme[key]

    payload = {
        "Calculation.CalculationMethod": str(int(resolved["CalculationMethod"])),
        "Calculation.vbmap": str(resolved["vbmap"]),
        "Calculation.Altitude": f"{float(resolved['Altitude']):.0f}",
        "Calculation.DirectionalFactor": str(int(resolved["DirectionalFactor"])),
        "Calculation.dShore": f"{float(resolved['dShore']):.1f}",
        "Calculation.dTown": str(int(resolved["dTown"])),
        "Calculation.z": f"{float(resolved['z']):.3f}",
        "Calculation.hdis": str(int(resolved["hdis"])),
        "Calculation.c0_z": str(resolved["c0_z"]),
        "Calculation.cseason": str(resolved["cseason"]),
        "__RequestVerificationToken": _REQUEST_VERIFICATION_TOKEN,
        "Calculation.Project": str(resolved["Project"]),
        "Calculation.Subject": str(resolved["Subject"]),
        "Calculation.Designer": str(resolved["Designer"]),
        "Calculation.Date": str(resolved["Date"]),
    }

    filename = f"scheme_{scheme_id}.json"
    json_path = output_dir / filename

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return json_path