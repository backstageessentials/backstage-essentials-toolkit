"""bes push command.

Pushes commits to the GitHub remote. Thin wrapper around git push.
"""

from pathlib import Path

from rich.console import Console

from ..helpers.config import find_course_root
from ..helpers import git

console = Console()


def run() -> int:
    """Run the push command. Returns exit code."""
    course_root = find_course_root() or Path.cwd()

    if not git.is_git_repo(course_root):
        console.print("[red]Not in a git repository.[/red]")
        return 1

    branch = git.current_branch(course_root)
    if not branch:
        console.print("[red]No current branch (detached HEAD?).[/red]")
        return 1

    ahead = git.commits_ahead_of_origin(course_root)
    if ahead == 0:
        console.print("[yellow]Nothing to push. Local branch is up to date with origin.[/yellow]")
        return 0

    console.print(f"[cyan]Pushing {ahead} commit(s) to origin/{branch}...[/cyan]")
    success, output = git.push(course_root)

    if not success:
        console.print(f"[red]Push failed:[/red]\n{output}")
        return 1

    console.print(f"[green]Pushed.[/green]")
    if output:
        for line in output.splitlines():
            console.print(f"  {line}")
    return 0
