"""Runner — executes the full wind automation pipeline:
1. run_first_scheme_cez  : fetches geodata, runs website automation, populates wind_example.xlsx
2. populate_wind_check_excel : writes results into the Wind Check Excel template
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def main() -> None:
    print("=" * 60)
    print("STEP 1: Running run_first_scheme_cez...")
    print("=" * 60)
    try:
        from scripts.run_first_scheme_cez import main as run_schemes
        run_schemes()
        print("STEP 1: Done.\n")
    except Exception:
        print("STEP 1: FAILED.")
        traceback.print_exc()
        sys.exit(1)

    print("=" * 60)
    print("STEP 2: Running populate_wind_check_excel...")
    print("=" * 60)
    try:
        from scripts.populate_wind_check_excel import main as populate_excel
        populate_excel()
        print("STEP 2: Done.\n")
    except Exception:
        print("STEP 2: FAILED.")
        traceback.print_exc()
        sys.exit(1)

    print("=" * 60)
    print("ALL STEPS COMPLETE.")
    print("=" * 60)


if __name__ == "__main__":
    main()
