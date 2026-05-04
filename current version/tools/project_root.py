# tools/project_root.py
"""Utility to locate the project root directory.

The project root is defined as the nearest parent folder (from this file
upward) that contains a 'tools' subfolder.

Usage:
    from tools.project_root import PROJECT_ROOT
"""

from pathlib import Path


def _find_project_root() -> Path:
    """Walk up from this file until we find the folder containing 'tools/'."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "tools").is_dir():
            return parent
    raise RuntimeError("Could not find project root (no parent folder contains 'tools/')")


PROJECT_ROOT = _find_project_root()
