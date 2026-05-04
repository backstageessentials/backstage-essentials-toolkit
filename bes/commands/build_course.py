"""bes build-course command.

The "do it all" command. Chains lesson drafting, quiz generation, and
final assessment building into a single end-to-end build of an entire
course based on the course description, voice guide, and unit titles.

Like the other content commands, this prepares a structured prompt for
Claude Code rather than running content generation directly. Building
a full course is a long task; the prompt instructs Claude Code to do
it in stages with confirmation between major steps.
"""

import click
from pathlib import Path

import yaml
from rich.console import Console

from ..helpers.config import find_course_root, load_config, ConfigError

console = Console()


def run(lessons_per_unit: int = 4, target_word_count: int = 800,
        questions_per_unit_kc: int = 8, total_final_questions: int = 200,
        confirm_each_unit: bool = True) -> int:
    """Run build-course command. Returns exit code."""
    course_root = find_course_root()
    if not course_root:
        console.print("[red]course-config.yaml not found. Are you inside a course repo?[/red]")
        return 1

    try:
        config = load_config(course_root)
    except ConfigError as e:
        console.print(f"[red]{e}[/red]")
        return 1

    # Verify the prerequisites
    desc_file = course_root / "course-description.md"
    voice_file = course_root / "voice-guide.md"

    if not desc_file.exists():
        console.print("[red]course-description.md is missing. Fill it in before building the course.[/red]")
        return 1
    if not voice_file.exists():
        console.print("[red]voice-guide.md is missing. Fill it in before building the course.[/red]")
        return 1

    desc_text = desc_file.read_text(encoding="utf-8")
    voice_text = voice_file.read_text(encoding="utf-8")

    if "[Insert your sample here]" in desc_text or "[Your Course Name]" in desc_text:
        console.print("[red]course-description.md still has unfilled template placeholders.[/red]")
        return 1
    if "[Insert your sample here]" in voice_text or "[Your Course Name]" in voice_text:
        console.print("[red]voice-guide.md still has unfilled template placeholders.[/red]")
        return 1

    # Check unit folders
    content_dir = course_root / "content"
    unit_folders = sorted(p for p in content_dir.glob("unit-*") if p.is_dir()) if content_dir.exists() else []
    if not unit_folders:
        console.print("[red]No unit folders in content/. Run 'bes new-course' first.[/red]")
        return 1

    # Check unit titles and outcomes are filled
    incomplete_units = []
    for unit_folder in unit_folders:
        unit_yaml = unit_folder / "unit.yaml"
        if not unit_yaml.exists():
            incomplete_units.append(f"{unit_folder.name}: missing unit.yaml")
            continue
        with unit_yaml.open() as f:
            data = yaml.safe_load(f) or {}
        unit = data.get("unit", {})
        if not unit.get("title") or unit.get("title") in ("", "Unit Title"):
            incomplete_units.append(f"{unit_folder.name}: missing title")
        if not unit.get("learning_outcomes"):
            incomplete_units.append(f"{unit_folder.name}: missing learning_outcomes")

    if incomplete_units:
        console.print("[red]Some unit.yaml files are not ready:[/red]")
        for issue in incomplete_units:
            console.print(f"  [red]{issue}[/red]")
        console.print("[yellow]Fill in unit titles and learning outcomes before running build-course.[/yellow]")
        return 1

    # Looks good. Build the prompt.
    estimated_lessons = lessons_per_unit * len(unit_folders)
    estimated_kc_questions = questions_per_unit_kc * len(unit_folders)
    total_questions = estimated_kc_questions + total_final_questions

    console.print()
    console.print(f"[green]Course is ready to build:[/green]")
    console.print(f"  Units:      {len(unit_folders)}")
    console.print(f"  Lessons:    ~{estimated_lessons} ({lessons_per_unit} per unit at {target_word_count} words each)")
    console.print(f"  KC questions: ~{estimated_kc_questions} ({questions_per_unit_kc} per unit)")
    console.print(f"  Final questions: {total_final_questions}")
    console.print(f"  Total content items: ~{estimated_lessons + total_questions}")
    console.print()
    console.print("[yellow]This is a large amount of content. Building it all at once is a long task.[/yellow]")
    console.print("[yellow]The prompt below tells Claude Code to build in stages with confirmation between units.[/yellow]")

    if not click.confirm("Continue and generate the prompt?", default=True):
        return 0

    prompt = _build_course_prompt(
        course_root=course_root,
        unit_folders=unit_folders,
        lessons_per_unit=lessons_per_unit,
        target_word_count=target_word_count,
        questions_per_unit_kc=questions_per_unit_kc,
        total_final_questions=total_final_questions,
        confirm_each_unit=confirm_each_unit,
    )

    console.print()
    console.print("[cyan]Paste this prompt into Claude Code:[/cyan]")
    console.print()
    console.print("=" * 70)
    console.print(prompt)
    console.print("=" * 70)
    console.print()
    console.print("[yellow]This will take a while. Claude Code will pause for your confirmation[/yellow]")
    console.print("[yellow]between major sections so you can review as it goes.[/yellow]")

    return 0


def _build_course_prompt(course_root: Path, unit_folders: list,
                          lessons_per_unit: int, target_word_count: int,
                          questions_per_unit_kc: int, total_final_questions: int,
                          confirm_each_unit: bool) -> str:
    """Build the megaprompt that drives a full course build."""
    confirm_text = (
        "After each unit (lessons + quiz), pause and ask me to review and confirm "
        "before moving to the next unit."
        if confirm_each_unit else
        "Build all units in sequence without pausing for confirmation."
    )

    unit_list = "\n".join(f"  - {u.name}" for u in unit_folders)

    return f"""Build the entire course end to end using the toolkit's content skills.

Course root: {course_root}
Units to build:
{unit_list}

Targets:
- Lessons per unit: {lessons_per_unit}
- Target word count per lesson: {target_word_count}
- Knowledge check questions per unit: {questions_per_unit_kc}
- Final assessment questions: {total_final_questions}

Confirmation strategy: {confirm_text}

Procedure:

PHASE A: Plan the course
1. Read course-description.md, voice-guide.md, and every unit.yaml.
2. For each unit, propose lesson topics that collectively achieve the unit's learning outcomes. \
{lessons_per_unit} lessons per unit. Each lesson should map to one or more outcomes.
3. Show me the proposed lesson topics for all units. WAIT for my confirmation before drafting.

PHASE B: Draft lessons unit by unit
For each unit:
4. Use the lesson-drafter skill to draft each lesson per the plan from Phase A.
5. Match the voice guide exactly. Stay within target word count plus or minus 20%.
6. Set draft: true in each lesson's frontmatter.
7. After all lessons in the unit are drafted, briefly show me file paths and word counts. \
{"Pause for my confirmation before moving on." if confirm_each_unit else "Continue to the next unit."}

PHASE C: Generate knowledge checks
For each unit:
8. Use the quiz-builder skill to generate {questions_per_unit_kc} questions per unit's knowledge-check.yaml.
9. Use scenario-based questions by default. Mix difficulty: 30% easy, 50% medium, 20% hard.
10. Set draft: true at the quiz level.

PHASE D: Generate the course final
11. Use the final-assessment-builder skill to generate {total_final_questions} questions in exam/course-final.yaml.
12. Distribute proportionally across units. Mix difficulty: 30% easy, 50% medium, 20% hard.
13. Avoid duplicating knowledge check questions.
14. Set draft: true.

PHASE E: Summary and next steps
15. Show me a final summary:
    - Total lessons created (per unit)
    - Total knowledge check questions (per unit)
    - Final assessment question count
    - Any warnings (incomplete coverage, voice drift, etc.)
16. Tell me to:
    - Read every lesson and revise anything that does not sound right
    - Spot-check the knowledge check questions per unit
    - Spot-check 10 to 20 questions in the final assessment
    - Set draft: false in frontmatter once a lesson or quiz has been reviewed
    - Run 'bes validate' to confirm everything is structurally sound
    - Run 'bes commit' and 'bes push' to save the work
    - Run 'bes sync' to push to the platform when ready

Important rules throughout:
- Never set draft: false. That is the human reviewer's job.
- Match the voice guide exactly in every lesson and every question.
- If you encounter ambiguity (a unit outcome that does not match a lesson topic, etc.), \
stop and ask me. Do not guess on architectural questions."""
