"""bes new-lesson command.

Prepares a prompt to draft a single lesson via the lesson-drafter skill.
Validates the input and outputs the prompt for Claude Code.
"""

from pathlib import Path

import click
from rich.console import Console

from ..helpers.config import find_course_root, load_config, ConfigError

console = Console()


def run(unit_number: int = None, lesson_topic: str = None,
        learning_outcome: str = None, target_word_count: int = 800,
        target_minutes: int = 12, lesson_type: str = "text") -> int:
    """Run new-lesson command. Returns exit code."""
    course_root = find_course_root()
    if not course_root:
        console.print("[red]course-config.yaml not found. Are you inside a course repo?[/red]")
        return 1

    try:
        config = load_config(course_root)
    except ConfigError as e:
        console.print(f"[red]{e}[/red]")
        return 1

    # Verify voice guide exists
    voice_guide = course_root / "voice-guide.md"
    if not voice_guide.exists():
        console.print("[red]voice-guide.md not found. Fill it in before drafting lessons.[/red]")
        console.print("[yellow]The toolkit's docs/voice-guide-template.md is the starting template.[/yellow]")
        return 1

    # Prompt for missing inputs
    if not unit_number:
        unit_number = click.prompt("Unit number", type=int)
    total_units = config.get("units", 6)
    if unit_number < 1 or unit_number > total_units:
        console.print(f"[red]Unit number must be between 1 and {total_units}.[/red]")
        return 1

    if not lesson_topic:
        lesson_topic = click.prompt("Lesson topic (one sentence)", type=str)
    if not learning_outcome:
        console.print("[cyan]Use a Bloom's verb: apply, demonstrate, evaluate, design, troubleshoot, recommend, etc.[/cyan]")
        console.print("[cyan]Avoid weak verbs: understand, know, learn, be aware of.[/cyan]")
        learning_outcome = click.prompt("Learning outcome", type=str)

    # Warn on weak verbs
    weak_verbs = ["understand", "know", "learn", "be aware", "appreciate",
                  "become familiar"]
    if any(v in learning_outcome.lower() for v in weak_verbs):
        if not click.confirm(
            "[yellow]The learning outcome uses a weak verb. Continue anyway?[/yellow]",
            default=False,
        ):
            console.print("Try a verb like: apply, demonstrate, evaluate, troubleshoot.")
            return 0

    prompt = _build_new_lesson_prompt(
        unit_number=unit_number,
        lesson_topic=lesson_topic,
        learning_outcome=learning_outcome,
        target_word_count=target_word_count,
        target_minutes=target_minutes,
        lesson_type=lesson_type,
        course_root=course_root,
    )

    console.print()
    console.print("[cyan]Next: paste this prompt into Claude Code[/cyan]")
    console.print(f"[cyan](make sure you are in {course_root} when you do):[/cyan]")
    console.print()
    console.print("=" * 70)
    console.print(prompt)
    console.print("=" * 70)
    console.print()
    console.print("[yellow]Claude Code will draft a lesson at the path it prints.[/yellow]")
    console.print("[yellow]Read it, revise anything that does not sound like you, then[/yellow]")
    console.print("[yellow]run 'bes commit' when ready to save.[/yellow]")

    return 0


def _build_new_lesson_prompt(unit_number: int, lesson_topic: str,
                              learning_outcome: str, target_word_count: int,
                              target_minutes: int, lesson_type: str,
                              course_root: Path) -> str:
    """Build the prompt for Claude Code."""
    return f"""Draft a new lesson using the lesson-drafter skill from the toolkit.

Inputs:
- unit_number: {unit_number}
- lesson_topic: "{lesson_topic}"
- learning_outcome: "{learning_outcome}"
- target_word_count: {target_word_count}
- target_minutes: {target_minutes}
- lesson_type: {lesson_type}

Steps:
1. Read the lesson-drafter SKILL.md from the toolkit (skills/lesson-drafter/SKILL.md).

2. Follow the skill's procedure:
   - Read course-description.md and voice-guide.md from the course root ({course_root})
   - Read the unit folder content/unit-{unit_number:02d}-*/ to understand context
   - Read existing lessons in the unit so you do not duplicate
   - Draft the lesson per the skill's output format
   - Match the voice guide exactly. No deviations.

3. Write the file to content/unit-{unit_number:02d}-*/lessons/NN-{{topic-slug}}.md \
where NN is the next available lesson number in the unit.

4. After writing, show me:
   - The file path you wrote to
   - Word count
   - The first paragraph (so I can sanity-check the voice)
   - Suggested next steps: review and revise, then 'bes commit' when ready

Set draft: true in the frontmatter so I know it has not been reviewed yet."""
