"""bes build-final command.

Prepares a prompt to generate the course final assessment via the
final-assessment-builder skill.
"""

import click
from pathlib import Path

from rich.console import Console

from ..helpers.config import find_course_root, load_config, ConfigError

console = Console()


def run(total_questions: int = 200, questions_per_attempt: int = 100,
        distribution: str = "proportional",
        difficulty_mix: str = "30 percent easy, 50 percent medium, 20 percent hard",
        assessment_style: str = "scenario") -> int:
    """Run build-final command. Returns exit code."""
    course_root = find_course_root()
    if not course_root:
        console.print("[red]course-config.yaml not found. Are you inside a course repo?[/red]")
        return 1

    try:
        config = load_config(course_root)
    except ConfigError as e:
        console.print(f"[red]{e}[/red]")
        return 1

    # Verify the content folder has lessons
    content_dir = course_root / "content"
    if not content_dir.exists():
        console.print("[red]content/ folder is missing.[/red]")
        return 1

    unit_folders = sorted(p for p in content_dir.glob("unit-*") if p.is_dir())
    if not unit_folders:
        console.print("[red]No unit folders found in content/.[/red]")
        return 1

    # Check that every unit has at least one lesson
    units_without_lessons = []
    total_lessons = 0
    for unit_folder in unit_folders:
        lessons_folder = unit_folder / "lessons"
        lessons = list(lessons_folder.glob("*.md")) if lessons_folder.exists() else []
        if not lessons:
            units_without_lessons.append(unit_folder.name)
        total_lessons += len(lessons)

    if units_without_lessons:
        console.print(f"[yellow]Warning: these units have no lessons yet: {', '.join(units_without_lessons)}[/yellow]")
        console.print("[yellow]The final will not generate questions for empty units.[/yellow]")
        if not click.confirm("Continue anyway?", default=False):
            return 0

    if total_questions < questions_per_attempt * 1.5:
        console.print(
            f"[yellow]Warning: total_questions ({total_questions}) is less than 1.5x[/yellow]\n"
            f"[yellow]questions_per_attempt ({questions_per_attempt}). Randomization will[/yellow]\n"
            f"[yellow]produce limited variety. Consider increasing total_questions.[/yellow]"
        )
        if not click.confirm("Continue anyway?", default=True):
            return 0

    prompt = _build_final_prompt(
        total_questions=total_questions,
        questions_per_attempt=questions_per_attempt,
        distribution=distribution,
        difficulty_mix=difficulty_mix,
        assessment_style=assessment_style,
        course_root=course_root,
        unit_count=len(unit_folders),
        total_lessons=total_lessons,
    )

    console.print()
    console.print(f"[green]Course has {len(unit_folders)} units and {total_lessons} lessons.[/green]")
    console.print(f"[green]Generating {total_questions} questions for the final assessment.[/green]")
    console.print()
    console.print("[cyan]Paste this prompt into Claude Code:[/cyan]")
    console.print()
    console.print("=" * 70)
    console.print(prompt)
    console.print("=" * 70)
    console.print()
    console.print("[yellow]This is high-stakes content. Review carefully before committing.[/yellow]")

    return 0


def _build_final_prompt(total_questions: int, questions_per_attempt: int,
                         distribution: str, difficulty_mix: str,
                         assessment_style: str, course_root: Path,
                         unit_count: int, total_lessons: int) -> str:
    """Build the prompt for Claude Code."""
    return f"""Generate the comprehensive course final assessment using the \
final-assessment-builder skill.

Inputs:
- total_questions: {total_questions}
- questions_per_attempt: {questions_per_attempt}
- distribution: {distribution}
- difficulty_mix: "{difficulty_mix}"
- assessment_style: {assessment_style}

Context:
- Course has {unit_count} units and {total_lessons} lessons total
- Course root: {course_root}

Steps:
1. Read the final-assessment-builder SKILL.md from the toolkit.

2. Follow the skill's procedure:
   - Read course-description.md and voice-guide.md
   - Read every unit.yaml for unit titles and outcomes
   - Read every lesson markdown for content context
   - Read existing knowledge-check.yaml files to avoid duplicating questions
   - Plan the distribution: {distribution} (see distribution-strategies.md)
   - Generate {total_questions} questions covering every lesson and outcome
   - Apply difficulty mix per unit: {difficulty_mix}
   - Each question has unique id (u{{N}}-q{{NN}} format)
   - Each has unit, difficulty, type, lesson_ref, learning_outcome_ref fields
   - Voice matches voice-guide.md throughout

3. Write the result to {course_root}/exam/course-final.yaml.
   Replace existing questions but preserve top-level fields (name, pass_threshold, etc.).

4. Set draft: true at the top level so course-validator flags it for review.

5. After writing, show me:
   - Total questions generated
   - Distribution by unit
   - Distribution by difficulty
   - First and last questions as sanity checks
   - Any units or learning outcomes that did not get coverage (warn me)"""
