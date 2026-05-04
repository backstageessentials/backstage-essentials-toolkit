"""bes commit command.

Stages and commits changes with a sensible message. If the user does not
provide a message, generates one from the diff.
"""

from pathlib import Path

from rich.console import Console

from ..helpers.config import find_course_root
from ..helpers import git

console = Console()


def run(message: str = None, stage_all: bool = True) -> int:
    """Run the commit command. Returns exit code."""
    course_root = find_course_root() or Path.cwd()

    if not git.is_git_repo(course_root):
        console.print("[red]Not in a git repository.[/red]")
        return 1

    if not git.has_uncommitted_changes(course_root):
        console.print("[yellow]No changes to commit.[/yellow]")
        return 0

    if stage_all:
        if not git.stage_all(course_root):
            console.print("[red]git add failed.[/red]")
            return 1

    files = git.list_changed_files(course_root)
    if not files:
        console.print("[yellow]Nothing staged. Use git add manually if you need partial commits.[/yellow]")
        return 0

    console.print(f"[cyan]Staging {len(files)} file(s):[/cyan]")
    for f in files[:10]:
        console.print(f"  {f}")
    if len(files) > 10:
        console.print(f"  ...and {len(files) - 10} more")

    if not message:
        message = git.auto_commit_message(course_root)
        console.print(f"[cyan]Auto-generated commit message:[/cyan] {message}")

    success, output = git.commit(course_root, message)
    if not success:
        console.print(f"[red]Commit failed:[/red]\n{output}")
        return 1

    console.print(f"[green]Committed:[/green] {output.splitlines()[0] if output else message}")
    return 0
