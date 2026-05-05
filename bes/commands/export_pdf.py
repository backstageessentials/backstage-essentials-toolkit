"""bes export-pdf command.

Generates a PDF of the current course regardless of its primary platform.
Useful for delivering a PDF asset alongside a Thinkific or Canvas course
without changing the course's platform setting.
"""

from pathlib import Path
from typing import Optional

from rich.console import Console

from ..helpers.config import find_course_root
from ..helpers.platform_router import get_export_pdf_function

console = Console()


def run(dry_run: bool = False, output_dir: Optional[str] = None) -> int:
    course_root = find_course_root()
    if not course_root:
        console.print(
            "[red]course-config.yaml not found. Are you inside a course repo?[/red]"
        )
        return 1

    export_pdf = get_export_pdf_function()
    out_dir = Path(output_dir).resolve() if output_dir else None
    return export_pdf(
        course_root=course_root,
        dry_run=dry_run,
        output_dir=out_dir,
    )
