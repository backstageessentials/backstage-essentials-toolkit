"""bes sync command.

Reads the platform from course-config.yaml and dispatches to the right
sync skill (sync/thinkific, sync/canvas, etc.).
"""

from pathlib import Path
from typing import Optional

from rich.console import Console

from ..helpers.config import find_course_root, load_config, ConfigError
from ..helpers.platform_router import get_sync_function, PlatformError

console = Console()


def run(dry_run: bool = False, force_update: bool = False,
        units_to_sync: Optional[list[int]] = None) -> int:
    """Run the sync command. Returns exit code."""
    course_root = find_course_root()
    if not course_root:
        console.print("[red]course-config.yaml not found. Are you inside a course repo?[/red]")
        return 1

    try:
        config = load_config(course_root)
    except ConfigError as e:
        console.print(f"[red]{e}[/red]")
        return 1

    platform = config.get("platform")
    try:
        sync_fn = get_sync_function(platform)
    except PlatformError as e:
        console.print(f"[red]{e}[/red]")
        return 1

    return sync_fn(
        course_root=course_root,
        dry_run=dry_run,
        force_update=force_update,
        units_to_sync=units_to_sync,
    )
