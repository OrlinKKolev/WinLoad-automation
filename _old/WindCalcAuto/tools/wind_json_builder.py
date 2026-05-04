"""JSON builder for the EurocodeApplied UK & Irish NA wind calculator.

Provides one public function:

    build_and_save_scheme_json(scheme: dict, output_dir: Path) -> Path

Receives a plain dict of scheme parameters, builds a JSON file that
matches the EurocodeApplied SAVE/LOAD format, saves it under output_dir,
and returns the path to the written file.

Nothing here touches Excel, a browser, or any external API.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Fixed token from a valid exported JSON.
# The site appears to accept this when loading configs through the UI.
_REQUEST_VERIFICATION_TOKEN = (
    "CfDJ8GyiMZkFCtpIndt9zBOb5jkiTMSFlOvb6r2j-lxIW1jk6-E2nv8uib2BOg59SfaL3ReQMeYWUjPt6OzoDbp2gPsEnSB7bfRXYmI65ltVk2FDbt4VBtxKb8mGObSIDDNq6bvL_ERfRD5U_WbnzFvjbak"
)


def build_and_save_scheme_json(scheme: dict[str, Any], output_dir: Path) -> Path:
    """Build a JSON config from a scheme dict and save it to output_dir.

    Parameters
    ----------
    scheme : dict with the following keys:
        Required:
            scheme_id       - identifier used as filename prefix and Calculation.Project
            H               - reference height z_e (m)
            DistanceToSea_km - upwind distance to shoreline (km)
            Elevation_m     - site altitude (m)
            vbmap           - basic wind velocity from NA map (m/s)
        Optional (defaults used if missing):
            DirectionalFactor   default 25
            dTown               default 0
            hdis                default 0
            c0_z                default 1
            cseason             default 1
            CalculationMethod   default 0
            Project             default to scheme_id
            Subject             default ''
            Designer            default ''
            Date                default ''

    output_dir : Path
        Directory where the JSON file will be written.  Created if it
        does not exist.

    Returns
    -------
    Path to the written JSON file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    scheme_id = str(scheme.get("scheme_id", "scheme"))

    payload = {
        "Calculation.CalculationMethod": str(int(scheme.get("CalculationMethod", 0))),
        "Calculation.vbmap": f"{float(scheme['vbmap']):.2f}",
        "Calculation.Altitude": f"{float(scheme.get('Elevation_m', 0)):.0f}",
        "Calculation.DirectionalFactor": str(int(scheme.get("DirectionalFactor", 25))),
        "Calculation.dShore": f"{float(scheme.get('DistanceToSea_km', 0)):.1f}",
        "Calculation.dTown": str(int(scheme.get("dTown", 0))),
        "Calculation.z": f"{float(scheme['H']):.3f}",
        "Calculation.hdis": str(int(scheme.get("hdis", 0))),
        "Calculation.c0_z": str(scheme.get("c0_z", 1)),
        "Calculation.cseason": str(scheme.get("cseason", 1)),
        "__RequestVerificationToken": _REQUEST_VERIFICATION_TOKEN,
        "Calculation.Project": str(scheme.get("Project", scheme_id)),
        "Calculation.Subject": str(scheme.get("Subject", "")),
        "Calculation.Designer": str(scheme.get("Designer", "")),
        "Calculation.Date": str(scheme.get("Date", "")),
    }

    filename = f"scheme_{scheme_id}.json"
    json_path = output_dir / filename

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return json_path
