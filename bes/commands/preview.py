"""bes preview and bes preview-final commands.

Convenience wrappers that render the static-web preview HTML for the
current course. These exist so the user does not have to drop into a
python REPL to regenerate previews.

- bes preview            -> course-preview.html (every unit, plus the
                            course final in test mode)
- bes preview-final      -> final-preview.html (just the final, in
                            test mode)
"""

import sys
from pathlib import Path

import click
from rich.console import Console

from ..helpers.config import find_course_root, ConfigError

console = Console()


def _output_dir(course_root: Path) -> Path:
    return course_root / "preview"


def _import_preview():
    """Import the toolkit's static-web preview module.

    The static-web sync folder is not a Python package importable by name
    because it has a hyphen, so we add its lib path to sys.path.
    """
    here = Path(__file__).resolve()
    toolkit_root = here.parent.parent.parent  # bes/commands/preview.py -> toolkit
    lib_path = toolkit_root / "sync" / "static-web" / "lib"
    if str(lib_path) not in sys.path:
        sys.path.insert(0, str(lib_path))
    import preview as _preview_mod  # noqa: WPS433 (deliberate dynamic import)
    return _preview_mod


def run_course(open_after: bool = False) -> int:
    """Render the course-level preview into ./preview/course-preview.html."""
    course_root = find_course_root()
    if not course_root:
        console.print("[red]course-config.yaml not found. Are you inside a course repo?[/red]")
        return 1
    preview_mod = _import_preview()
    out_dir = _output_dir(course_root)
    out_path = preview_mod.write_course_preview(course_root, out_dir)
    console.print(f"[green]Wrote:[/green] {out_path}")
    if open_after:
        click.launch(str(out_path))
    return 0


def run_final(open_after: bool = False) -> int:
    """Render the final-only preview into ./preview/final-preview.html."""
    course_root = find_course_root()
    if not course_root:
        console.print("[red]course-config.yaml not found. Are you inside a course repo?[/red]")
        return 1
    preview_mod = _import_preview()
    out_dir = _output_dir(course_root)
    out_path = preview_mod.write_final_preview(course_root, out_dir)
    console.print(f"[green]Wrote:[/green] {out_path}")
    if open_after:
        click.launch(str(out_path))
    return 0
