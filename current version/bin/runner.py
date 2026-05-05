"""Runner — executes the full wind automation pipeline:
1. process_schemes   : reads input, resolves geo, routes UK/EU, writes output Excel
2. generate_reports  : fills Wind Check workbooks and exports PDFs
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def main() -> None:
    print("=" * 60)
    print("STEP 1: Processing schemes...")
    print("=" * 60)
    try:
        from app.pipeline.process_schemes import main as process_schemes
        process_schemes()
        print("STEP 1: Done.\n")
    except Exception:
        print("STEP 1: FAILED.")
        traceback.print_exc()
        sys.exit(1)

    print("=" * 60)
    print("STEP 2: Generating reports...")
    print("=" * 60)
    try:
        from app.pipeline.generate_reports import main as generate_reports
        generate_reports()
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