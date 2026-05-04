"""bes new-quiz command.

Prepares a prompt to generate a unit's knowledge check questions via the
quiz-builder skill.
"""

import click
from pathlib import Path

from rich.console import Console

from ..helpers.config import find_course_root, load_config, ConfigError

console = Console()


def run(unit_number: int = None, num_questions: int = 8,
        assessment_style: str = "scenario",
        difficulty_mix: str = "mostly medium with some easy and hard") -> int:
    """Run new-quiz command. Returns exit code."""
    course_root = find_course_root()
    if not course_root:
        console.print("[red]course-config.yaml not found. Are you inside a course repo?[/red]")
        return 1

    try:
        config = load_config(course_root)
    except ConfigError as e:
        console.print(f"[red]{e}[/red]")
        return 1

    if not unit_number:
        unit_number = click.prompt("Unit number", type=int)
    total_units = config.get("units", 6)
    if unit_number < 1 or unit_number > total_units:
        console.print(f"[red]Unit number must be between 1 and {total_units}.[/red]")
        return 1

    # Verify the unit has lessons to base questions on
    unit_glob = list((course_root / "content").glob(f"unit-{unit_number:02d}-*"))
    if not unit_glob:
        console.print(f"[red]No folder found for unit {unit_number}.[/red]")
        return 1
    unit_folder = unit_glob[0]
    lessons_folder = unit_folder / "lessons"
    lesson_files = list(lessons_folder.glob("*.md")) if lessons_folder.exists() else []
    if not lesson_files:
        console.print(f"[red]Unit {unit_number} has no lessons yet. Draft lessons first with 'bes new-lesson'.[/red]")
        return 1

    prompt = _build_new_quiz_prompt(
        unit_number=unit_number,
        num_questions=num_questions,
        assessment_style=assessment_style,
        difficulty_mix=difficulty_mix,
        unit_folder=unit_folder,
        lesson_count=len(lesson_files),
    )

    console.print()
    console.print(f"[green]Unit {unit_number} has {len(lesson_files)} lesson(s) to base questions on.[/green]")
    console.print()
    console.print("[cyan]Paste this prompt into Claude Code:[/cyan]")
    console.print()
    console.print("=" * 70)
    console.print(prompt)
    console.print("=" * 70)
    console.print()
    console.print("[yellow]After Claude Code finishes, review the questions, revise as needed,[/yellow]")
    console.print("[yellow]then run 'bes commit' to save.[/yellow]")

    return 0


def _build_new_quiz_prompt(unit_number: int, num_questions: int,
                            assessment_style: str, difficulty_mix: str,
                            unit_folder: Path, lesson_count: int) -> str:
    """Build the prompt for Claude Code."""
    return f"""Generate a knowledge check for a unit using the quiz-builder skill.

Inputs:
- unit_number: {unit_number}
- num_questions: {num_questions}
- assessment_style: {assessment_style}
- difficulty_mix: "{difficulty_mix}"

Context:
- The unit has {lesson_count} lesson(s) at {unit_folder}/lessons/
- Read the existing knowledge-check.yaml at {unit_folder}/knowledge-check.yaml \
to preserve title and pass_threshold

Steps:
1. Read the quiz-builder SKILL.md from the toolkit.

2. Follow the skill's procedure:
   - Read course-description.md and voice-guide.md
   - Read every lesson in {unit_folder}/lessons/
   - Read the unit's unit.yaml for unit-level outcomes
   - Generate {num_questions} questions covering all lessons
   - Use the {assessment_style} style
   - Apply difficulty mix: {difficulty_mix}
   - Each question gets a unique id (u{unit_number}-kc-NN format)
   - Each has 2-4 choices with at least one correct
   - Each has an explanation that teaches, not just confirms

3. Write the result to {unit_folder}/knowledge-check.yaml. Replace existing \
placeholder questions but preserve the title and pass_threshold from the file.

4. Set draft: true at the quiz level.

5. After writing, show me a count of questions per difficulty level and the \
first question as a sanity check."""
