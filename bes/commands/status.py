"""bes status command.

Shows what's pending: uncommitted changes, commits not yet pushed,
last sync time. The "is this course in sync with everything" snapshot.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table

from ..helpers.config import find_course_root, load_config, ConfigError
from ..helpers import git

console = Console()


def run() -> int:
    """Show status. Returns 0 always (informational only)."""
    course_root = find_course_root()
    if not course_root:
        console.print("[red]course-config.yaml not found. Are you inside a course repo?[/red]")
        return 1

    try:
        config = load_config(course_root)
    except ConfigError as e:
        console.print(f"[red]{e}[/red]")
        return 1

    table = Table(title=config.get("name", "Course"), show_header=False, box=None)
    table.add_column(style="cyan", justify="right")
    table.add_column()

    table.add_row("Slug:", config.get("slug", "(none)"))
    table.add_row("Platform:", config.get("platform", "(none)"))
    table.add_row("Path:", str(course_root))

    # Git status
    if git.is_git_repo(course_root):
        branch = git.current_branch(course_root) or "(detached)"
        changed = git.list_changed_files(course_root)
        ahead = git.commits_ahead_of_origin(course_root)

        table.add_row("Branch:", branch)
        if changed:
            table.add_row("Uncommitted:", f"[yellow]{len(changed)} file(s)[/yellow]")
        else:
            table.add_row("Uncommitted:", "[green]none[/green]")
        if ahead > 0:
            table.add_row("Unpushed:", f"[yellow]{ahead} commit(s)[/yellow]")
        else:
            table.add_row("Unpushed:", "[green]none[/green]")

    # Sync state
    sync_state_file = course_root / "sync-state.json"
    if sync_state_file.exists():
        try:
            with sync_state_file.open() as f:
                state = json.load(f)
            last_sync = state.get("last_sync")
            if last_sync:
                table.add_row("Last sync:", _humanize_timestamp(last_sync))
            course_id = state.get("course_id")
            if course_id:
                table.add_row("Platform course ID:", str(course_id))
        except (json.JSONDecodeError, OSError):
            table.add_row("Sync state:", "[red]unreadable[/red]")
    else:
        table.add_row("Last sync:", "[yellow]never[/yellow]")

    console.print()
    console.print(table)
    console.print()

    # Suggest next steps
    if git.is_git_repo(course_root):
        changed = git.list_changed_files(course_root)
        ahead = git.commits_ahead_of_origin(course_root)
        suggestions = []
        if changed:
            suggestions.append("[yellow]bes commit[/yellow] to commit your changes")
        if ahead > 0:
            suggestions.append("[yellow]bes push[/yellow] to push to GitHub")
        if not (course_root / "sync-state.json").exists():
            suggestions.append("[yellow]bes sync[/yellow] to push to the platform (first time)")
        if suggestions:
            console.print("Suggested:")
            for s in suggestions:
                console.print(f"  {s}")

    return 0


def _humanize_timestamp(iso_string: str) -> str:
    """Convert an ISO timestamp to a relative readable form."""
    try:
        ts = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    except ValueError:
        return iso_string
    delta = datetime.now(timezone.utc) - ts
    seconds = delta.total_seconds()
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)} minute(s) ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)} hour(s) ago"
    days = int(seconds // 86400)
    return f"{days} day(s) ago"
