#!/usr/bin/env python3
"""
Course-local sync shim (PDF).

This file lives in your course repo at scripts/sync.py. It exists so that
running `python3 scripts/sync.py` works from inside the course folder
without requiring the bes command to be installed.

The actual rendering logic lives in the toolkit. This shim imports it and
runs it.

Usage:
    python3 scripts/sync.py             # generate the PDF
    python3 scripts/sync.py --dry-run   # write the intermediate HTML only

For richer command line options and access to all bes commands, install bes:
    pip install -e ~/Code/backstage-essentials-toolkit
Then use:
    bes sync          # if course-config.yaml platform is pdf
    bes export-pdf    # at any time, regardless of primary platform
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Render the course as a PDF.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Write the intermediate HTML only; skip the PDF render.")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Where to write the PDF (default: ./build/pdf).")
    args = parser.parse_args()

    try:
        from sync.pdf.lib import sync
    except ImportError:
        print("Could not import the Backstage Essentials Toolkit.")
        print()
        print("Install it from your local clone:")
        print("  cd ~/Code/backstage-essentials-toolkit")
        print("  pip install -e .")
        print()
        print("Or update the path in this file if your toolkit lives elsewhere.")
        sys.exit(1)

    course_root = Path(__file__).parent.parent.resolve()
    exit_code = sync(
        course_root=course_root,
        dry_run=args.dry_run,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
