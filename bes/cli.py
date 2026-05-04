"""bes command line interface.

Wires up Click commands and dispatches to the right command module.
"""

import sys

import click
from rich.console import Console

from . import __version__
from .commands import validate as validate_cmd
from .commands import sync as sync_cmd
from .commands import commit as commit_cmd
from .commands import push as push_cmd
from .commands import status as status_cmd

console = Console()


@click.group(
    help="Backstage Essentials Course Builder Toolkit (bes).\n\n"
    "Run 'bes COMMAND --help' for details on a specific command.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(__version__, prog_name="bes")
def main():
    """Top-level bes command group."""


@main.command()
@click.option("--strict", is_flag=True,
              help="Treat warnings as errors (fail the validation).")
def validate(strict: bool):
    """Check the current course repo for problems."""
    exit_code = validate_cmd.run(strict=strict)
    sys.exit(exit_code)


@main.command()
@click.option("--dry-run", is_flag=True,
              help="Validate content without pushing to the platform.")
@click.option("--force", "force_update", is_flag=True,
              help="Re-push everything regardless of change detection.")
@click.option("--units", "units_to_sync", default=None,
              help="Comma-separated unit numbers to sync (default: all).")
def sync(dry_run: bool, force_update: bool, units_to_sync: str):
    """Push course content to the platform configured in course-config.yaml."""
    units_list = None
    if units_to_sync:
        try:
            units_list = [int(u.strip()) for u in units_to_sync.split(",")]
        except ValueError:
            console.print("[red]--units must be comma-separated integers (e.g., 1,2,4)[/red]")
            sys.exit(1)
    exit_code = sync_cmd.run(
        dry_run=dry_run,
        force_update=force_update,
        units_to_sync=units_list,
    )
    sys.exit(exit_code)


@main.command()
@click.option("-m", "--message", default=None,
              help="Commit message. If omitted, bes generates one from the diff.")
@click.option("--all", "stage_all", is_flag=True, default=True,
              help="Stage all changes before committing (default).")
def commit(message: str, stage_all: bool):
    """Stage changes and commit them with a sensible message."""
    exit_code = commit_cmd.run(message=message, stage_all=stage_all)
    sys.exit(exit_code)


@main.command()
def push():
    """Push commits to the GitHub remote."""
    exit_code = push_cmd.run()
    sys.exit(exit_code)


@main.command()
def status():
    """Show what's pending: uncommitted changes, unsynced content, last sync time."""
    exit_code = status_cmd.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
