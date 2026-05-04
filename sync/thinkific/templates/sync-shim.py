#!/usr/bin/env python3
"""
Course-local sync shim.

This file lives in your course repo at scripts/sync.py. It exists so that
running `python3 scripts/sync.py` works from inside the course folder
without requiring the bes command to be installed.

The actual sync logic lives in the toolkit. This shim imports it and runs it.

Usage:
    python3 scripts/sync.py             # normal sync
    python3 scripts/sync.py --dry-run   # validate without pushing
    python3 scripts/sync.py --force     # re-push everything

For richer command line options and access to all bes commands, install bes:
    pip install -e ~/Code/backstage-essentials-toolkit
Then use:
    bes sync --dry-run
    bes sync --force-update
    bes sync --units 1,2,4
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Sync course content to Thinkific.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate content without pushing to Thinkific")
    parser.add_argument("--force", action="store_true",
                        help="Re-push everything regardless of change detection")
    parser.add_argument("--units", type=str, default=None,
                        help="Comma-separated unit numbers to sync (default: all)")
    args = parser.parse_args()

    units_to_sync = None
    if args.units:
        units_to_sync = [int(u) for u in args.units.split(",")]

    # Try to import the toolkit. If not installed, give a clear error.
    try:
        from bes_toolkit.sync.thinkific.lib import sync
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
        force_update=args.force,
        units_to_sync=units_to_sync,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
