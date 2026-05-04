"""bes add-microsim command.

Prepares a prompt for Claude Code to run the microsim-builder skill against
a single lesson, customizing one of the seven starter templates.
"""

import re
import click
from pathlib import Path

from rich.console import Console

from ..helpers.config import find_course_root, load_config, ConfigError

console = Console()

TEMPLATE_TYPES = [
    "signal-flow", "calculator", "flashcards", "decision-tree",
    "timeline", "matcher", "formula",
]


def run(unit_number: int = None,
        lesson_filename: str = None,
        template_type: str = None,
        sim_filename: str = None,
        height: int = 400) -> int:
    """Run add-microsim command. Returns exit code."""
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
        unit_number = click.prompt(f"Unit number (1-{total_units})", type=int)
    if unit_number < 1 or unit_number > total_units:
        console.print(f"[red]Unit number must be between 1 and {total_units}.[/red]")
        return 1

    unit_glob = list((course_root / "content").glob(f"unit-{unit_number:02d}-*"))
    if not unit_glob:
        console.print(f"[red]No folder found for unit {unit_number}.[/red]")
        return 1
    unit_folder = unit_glob[0]
    lessons_folder = unit_folder / "lessons"
    lesson_files = sorted(lessons_folder.glob("*.md")) if lessons_folder.exists() else []
    if not lesson_files:
        console.print(f"[red]Unit {unit_number} has no lessons. Draft lessons first with 'bes new-lesson'.[/red]")
        return 1

    if lesson_filename is None:
        console.print("Lessons in this unit:")
        for i, lf in enumerate(lesson_files, start=1):
            console.print(f"  {i}. {lf.name}")
        choice = click.prompt("Pick a lesson by number or paste the filename", type=str)
        try:
            lesson_filename = lesson_files[int(choice.strip()) - 1].name
        except (ValueError, IndexError):
            lesson_filename = choice.strip()

    lesson_path = lessons_folder / lesson_filename
    if not lesson_path.exists():
        console.print(f"[red]Lesson not found: {lesson_path}[/red]")
        return 1

    if template_type is None:
        template_type = click.prompt(
            f"Template type ({', '.join(TEMPLATE_TYPES)})",
            type=click.Choice(TEMPLATE_TYPES),
        )
    if template_type not in TEMPLATE_TYPES:
        console.print(f"[red]Template type must be one of: {', '.join(TEMPLATE_TYPES)}[/red]")
        return 1

    if sim_filename is None:
        # Derive from lesson stem and template type
        stem = re.sub(r"^\d+-", "", lesson_path.stem)
        sim_filename = f"{stem}-{template_type}.html"
    if not sim_filename.endswith(".html"):
        sim_filename = sim_filename + ".html"

    template_filename = {
        "signal-flow": "signal-flow-visualizer.html",
        "calculator": "circuit-load-calculator.html",
        "flashcards": "flashcard-deck.html",
        "decision-tree": "decision-tree-explorer.html",
        "timeline": "timeline-scrubber.html",
        "matcher": "drag-and-drop-matcher.html",
        "formula": "formula-explorer.html",
    }[template_type]

    prompt = _build_add_microsim_prompt(
        unit_number=unit_number,
        unit_folder=unit_folder,
        lesson_path=lesson_path,
        template_type=template_type,
        template_filename=template_filename,
        sim_filename=sim_filename,
        height=height,
    )

    console.print()
    console.print(f"[green]Lesson: {lesson_path}[/green]")
    console.print(f"[green]Template: {template_type} ({template_filename})[/green]")
    console.print(f"[green]MicroSim file will be saved at: {unit_folder}/microsims/{sim_filename}[/green]")
    console.print()
    console.print("[cyan]Paste this prompt into Claude Code:[/cyan]")
    console.print()
    console.print("=" * 70)
    console.print(prompt, markup=False, highlight=False)
    console.print("=" * 70)
    console.print()
    console.print("[yellow]After Claude Code finishes, render the preview, click around the[/yellow]")
    console.print("[yellow]MicroSim, then run 'bes commit' to save.[/yellow]")
    return 0


def _build_add_microsim_prompt(unit_number: int, unit_folder: Path, lesson_path: Path,
                                template_type: str, template_filename: str,
                                sim_filename: str, height: int) -> str:
    return f"""Add a MicroSim to one lesson using the microsim-builder skill.

Inputs:
- unit_number: {unit_number}
- lesson_filename: "{lesson_path.name}"
- template_type: {template_type}
- sim_filename: "{sim_filename}"
- height: {height}

Context:
- Lesson path: {lesson_path}
- Template path: skills/microsim-builder/templates/{template_filename}
- MicroSim output path: {unit_folder}/microsims/{sim_filename}

Steps:

1. Read the microsim-builder SKILL.md, microsim-patterns.md,
   p5js-template-reference.md, and simulation-types-reference.md from the
   toolkit.

2. Read the course-description.md and voice-guide.md from the course root
   for voice context. Every UI label, button text, intro line, and
   instruction inside the MicroSim must follow the voice guide.

3. Read the lesson markdown at {lesson_path}. Identify the concept the
   {template_type} MicroSim should teach (the manipulation the student
   should do).

4. Read the template at skills/microsim-builder/templates/{template_filename}.
   Find the <!-- CUSTOMIZE --> ... END CUSTOMIZE --> block. The CONFIG
   object inside that block is the only thing the skill rewrites; the
   machinery below the marker is shared and stays untouched.

5. Customize the CONFIG object for this lesson. Populate every field with
   voice-matched strings: title, intro, button labels, item labels, ranges,
   formulas, results, etc. See simulation-types-reference.md for the
   per-template field schemas.

6. Run the lint pattern from microsim-builder/SKILL.md:
   - Starts with <!DOCTYPE html>
   - Balanced <html>, <head>, <body>, <script> tags
   - Both <!-- CUSTOMIZE --> and END CUSTOMIZE --> markers present
   - No leftover template placeholders ({{TITLE}}, {{INTRO}}, etc.)

7. Save the customized HTML to {unit_folder}/microsims/{sim_filename}.
   Create the microsims/ folder if it does not already exist.

8. Edit the lesson markdown at {lesson_path} to insert the directive at
   the right spot (after the section heading and the first paragraph that
   introduces the simulated concept; never as the first thing in the
   lesson; never inside the wrap section). The directive line is:

       {{{{microsim: {sim_filename} height={height}}}}}

   Place a one-sentence intro line ending in a colon directly above the
   directive, in the lesson's voice (for example: "Try the decision rule
   yourself:").

9. Set draft: true on the lesson's frontmatter if not already true.

10. After writing both files, show me a summary:
    - Path to the saved MicroSim HTML
    - Path to the modified lesson markdown
    - The customize-block fields you populated and any voice concerns
      worth a human glance
    - Suggested next step: render the preview with sync/static-web and
      eyeball the MicroSim in a browser before committing."""
