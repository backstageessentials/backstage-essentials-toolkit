"""bes add-diagrams command.

Prepares a prompt for Claude Code to run the diagram-builder skill against
one unit (or every unit) and add Mermaid diagrams where they fit.
"""

import click
from pathlib import Path

from rich.console import Console

from ..helpers.config import find_course_root, load_config, ConfigError

console = Console()


def run(unit_number: int = None,
        max_diagrams_per_lesson: int = 3,
        min_diagrams_per_lesson: int = 1,
        allowed_types: str = "flowchart,sequence,state,class",
        lesson_filter: str = None) -> int:
    """Run add-diagrams command. Returns exit code."""
    course_root = find_course_root()
    if not course_root:
        console.print("[red]course-config.yaml not found. Are you inside a course repo?[/red]")
        return 1

    try:
        config = load_config(course_root)
    except ConfigError as e:
        console.print(f"[red]{e}[/red]")
        return 1

    total_units = config.get("units", 6)

    if unit_number is None:
        # No unit specified: prompt the user, defaulting to "all"
        choice = click.prompt(
            f"Unit number to add diagrams to (1-{total_units}, or 'all')",
            default="all",
        )
        if str(choice).strip().lower() == "all":
            unit_number = None
        else:
            try:
                unit_number = int(choice)
            except ValueError:
                console.print("[red]Unit number must be an integer or 'all'.[/red]")
                return 1

    if unit_number is not None:
        if unit_number < 1 or unit_number > total_units:
            console.print(f"[red]Unit number must be between 1 and {total_units}.[/red]")
            return 1
        unit_glob = list((course_root / "content").glob(f"unit-{unit_number:02d}-*"))
        if not unit_glob:
            console.print(f"[red]No folder found for unit {unit_number}.[/red]")
            return 1
        unit_folders = unit_glob
    else:
        unit_folders = sorted((course_root / "content").glob("unit-*"))
        if not unit_folders:
            console.print("[red]No unit folders found under content/.[/red]")
            return 1

    # Verify each target unit has at least one lesson
    targets = []
    for folder in unit_folders:
        lessons_dir = folder / "lessons"
        lesson_files = sorted(lessons_dir.glob("*.md")) if lessons_dir.exists() else []
        if not lesson_files:
            console.print(f"[yellow]Skipping {folder.name}: no lessons yet.[/yellow]")
            continue
        targets.append((folder, lesson_files))

    if not targets:
        console.print("[red]No units have lessons to add diagrams to. Draft lessons first with 'bes new-lesson'.[/red]")
        return 1

    types_list = [t.strip() for t in allowed_types.split(",") if t.strip()]
    prompt = _build_add_diagrams_prompt(
        targets=targets,
        max_diagrams_per_lesson=max_diagrams_per_lesson,
        min_diagrams_per_lesson=min_diagrams_per_lesson,
        allowed_types=types_list,
        lesson_filter=lesson_filter,
    )

    total_lessons = sum(len(lessons) for _, lessons in targets)
    console.print()
    console.print(
        f"[green]Targeting {len(targets)} unit(s) with {total_lessons} lesson(s) total.[/green]"
    )
    console.print()
    console.print("[cyan]Paste this prompt into Claude Code:[/cyan]")
    console.print()
    console.print("=" * 70)
    console.print(prompt)
    console.print("=" * 70)
    console.print()
    console.print("[yellow]After Claude Code finishes, eyeball the preview HTML, revise any[/yellow]")
    console.print("[yellow]diagrams that read off, then run 'bes commit' to save.[/yellow]")

    return 0


def _build_add_diagrams_prompt(targets: list[tuple[Path, list[Path]]],
                                max_diagrams_per_lesson: int,
                                min_diagrams_per_lesson: int,
                                allowed_types: list[str],
                                lesson_filter: str | None) -> str:
    """Build the prompt for Claude Code."""
    targets_block = "\n".join(
        f"- {folder.name}: {len(lessons)} lesson(s) at {folder}/lessons/"
        for folder, lessons in targets
    )
    types_csv = ", ".join(allowed_types)
    filter_line = (
        f'\n- lesson_filter: "{lesson_filter}" (only lessons matching this glob)'
        if lesson_filter else ""
    )

    return f"""Add Mermaid diagrams to existing lessons using the diagram-builder skill.

Inputs:
- max_diagrams_per_lesson: {max_diagrams_per_lesson}
- min_diagrams_per_lesson: {min_diagrams_per_lesson}
- allowed_types: [{types_csv}]{filter_line}

Targets:
{targets_block}

Steps:

1. Read the diagram-builder SKILL.md, diagram-patterns.md, and
   mermaid-syntax-reference.md from the toolkit.

2. For each target unit, follow the skill's procedure:
   - Read course-description.md and voice-guide.md for voice context.
   - Read each lesson markdown in the unit.
   - For each lesson, decide whether one to {max_diagrams_per_lesson} diagrams \
would teach the content better than prose alone. Most lessons get zero or \
one. The bar is high: a diagram earns its place only when prose cannot \
teach the structure as cleanly.
   - Choose the diagram type from the allowed list.
   - Draft the Mermaid syntax with short, voice-matched node labels.
   - Run the lint pattern from mermaid-syntax-reference.md before writing.
   - Insert the diagram inline at the right spot, with a one-sentence intro \
line ending in a colon above the fenced ```mermaid``` block.
   - Set draft: true on the lesson's frontmatter if not already true.

3. Skip any lesson that already has a Mermaid block at the spot you would \
have chosen. Do not overwrite or duplicate existing diagrams.

4. After all updates, show me a summary table:
   - For each modified lesson: file path, diagrams added, types used
   - For each skipped lesson: file path, reason (no good fit / already had one)
   - Suggested next step: render the unit preview with the static-web \
preview generator and eyeball the diagrams in a browser before committing."""
