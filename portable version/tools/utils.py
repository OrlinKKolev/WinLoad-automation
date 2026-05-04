"""
Shared utility helpers for Wind Calc Auto.
"""

from __future__ import annotations


def parse_number(value) -> float:
    """
    Convert an Excel cell value to float, handling both comma and dot
    as decimal separators.

    Handles:
        "-3,12"  →  -3.12
        "-3.12"  →  -3.12
        "3,12"   →   3.12
        "3.12"   →   3.12
        30       →  30.0   (already numeric — passed straight through)
        None/NaN →  raises ValueError
    """
    if value is None:
        raise ValueError("Cannot parse number: value is None")

    import math
    import pandas as pd

    if isinstance(value, float) and math.isnan(value):
        raise ValueError("Cannot parse number: value is NaN")

    if isinstance(value, (int, float)):
        return float(value)

    # String handling
    s = str(value).strip()
    if not s:
        raise ValueError("Cannot parse number: value is empty string")

    # Replace comma decimal separator with dot
    s = s.replace(",", ".")

    try:
        return float(s)
    except ValueError:
        raise ValueError(f"Cannot parse number: '{value}' is not a valid number")

def pause_for_inspection(message: str = "Inspect the results and then press Enter to continue...") -> None:
    """Pause execution and wait for user to press Enter.
    Call this anywhere during development/debugging to inspect browser state.
    Remove or comment out the call when done."""
    input(message)
