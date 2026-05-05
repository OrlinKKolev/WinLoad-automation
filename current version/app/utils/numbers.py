from __future__ import annotations


def parse_number(value):
    """Parse Excel / mixed numeric input into float.

    Accepts ints, floats, numeric strings, and strings with commas.
    Returns float or raises ValueError for invalid values.
    """
    if value is None:
        raise ValueError("Value is None")

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        raise ValueError("Empty numeric value")

    text = text.replace(",", "")
    return float(text)