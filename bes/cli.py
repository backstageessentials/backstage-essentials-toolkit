"""bes command line interface.

Wires up Click commands and dispatches to the right command module.

Phase 2.5 commands: validate, sync, commit, push, status
Phase 3 commands: new-course, new-lesson, new-quiz, build-final, build-course
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
from .commands import new_course as new_course_cmd
from .commands import new_lesson as new_lesson_cmd
from .commands import new_quiz as new_quiz_cmd
from .commands import build_final as build_final_cmd
from .commands import build_course as build_course_cmd
from .commands import add_diagrams as add_diagrams_cmd

console = Console()


@click.group(
    help="Backstage Essentials Course Builder Toolkit (bes).\n\n"
    "Run 'bes COMMAND --help' for details on a specific command.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(__version__, prog_name="bes")
def main():
    """Top-level bes command group."""


# ---------------- Phase 2.5: validation, git, sync ----------------

@main.command()
@click.option("--strict", is_flag=True,
              help="Treat warnings as errors (fail the validation).")
def validate(strict: bool):
    """Check the current course repo for problems."""
    sys.exit(validate_cmd.run(strict=strict))


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
    sys.exit(sync_cmd.run(
        dry_run=dry_run,
        force_update=force_update,
        units_to_sync=units_list,
    ))


@main.command()
@click.option("-m", "--message", default=None,
              help="Commit message. If omitted, bes generates one from the diff.")
@click.option("--all", "stage_all", is_flag=True, default=True,
              help="Stage all changes before committing (default).")
def commit(message: str, stage_all: bool):
    """Stage changes and commit them with a sensible message."""
    sys.exit(commit_cmd.run(message=message, stage_all=stage_all))


@main.command()
def push():
    """Push commits to the GitHub remote."""
    sys.exit(push_cmd.run())


@main.command()
def status():
    """Show what's pending: uncommitted changes, unsynced content, last sync time."""
    sys.exit(status_cmd.run())


# ---------------- Phase 3: course building ----------------

@main.command(name="new-course")
@click.option("--name", "course_name", default=None, help="Course name.")
@click.option("--platform", "target_platform", default=None,
              type=click.Choice(["thinkific", "canvas", "google-classroom",
                                "static-web", "pdf"]),
              help="Target platform (default: thinkific).")
@click.option("--units", "unit_count", default=6, type=int,
              help="Number of units in the course (default: 6).")
@click.option("--path", "output_path", default=".",
              help="Where to create the course folder (default: current directory).")
def new_course(course_name: str, target_platform: str, unit_count: int,
                output_path: str):
    """Bootstrap a new course folder with build spec and folder structure."""
    sys.exit(new_course_cmd.run(
        course_name=course_name,
        target_platform=target_platform,
        unit_count=unit_count,
        output_path=output_path,
    ))


@main.command(name="new-lesson")
@click.option("--unit", "unit_number", default=None, type=int, help="Unit number.")
@click.option("--topic", "lesson_topic", default=None, help="Lesson topic.")
@click.option("--outcome", "learning_outcome", default=None,
              help="Learning outcome (use Bloom's verb: apply, demonstrate, etc.)")
@click.option("--words", "target_word_count", default=800, type=int,
              help="Target word count (default: 800).")
@click.option("--minutes", "target_minutes", default=12, type=int,
              help="Target reading minutes (default: 12).")
@click.option("--type", "lesson_type", default="text",
              type=click.Choice(["text", "video-script", "hybrid"]),
              help="Lesson type (default: text).")
def new_lesson(unit_number: int, lesson_topic: str, learning_outcome: str,
                target_word_count: int, target_minutes: int, lesson_type: str):
    """Draft a new lesson via the lesson-drafter skill."""
    sys.exit(new_lesson_cmd.run(
        unit_number=unit_number,
        lesson_topic=lesson_topic,
        learning_outcome=learning_outcome,
        target_word_count=target_word_count,
        target_minutes=target_minutes,
        lesson_type=lesson_type,
    ))


@main.command(name="new-quiz")
@click.option("--unit", "unit_number", default=None, type=int, help="Unit number.")
@click.option("--questions", "num_questions", default=8, type=int,
              help="Number of questions (default: 8).")
@click.option("--style", "assessment_style", default="scenario",
              type=click.Choice(["scenario", "recall", "applied-calculation", "mixed"]),
              help="Assessment style (default: scenario).")
@click.option("--difficulty", "difficulty_mix",
              default="mostly medium with some easy and hard",
              help="Difficulty mix description.")
def new_quiz(unit_number: int, num_questions: int, assessment_style: str,
              difficulty_mix: str):
    """Generate a unit's knowledge check questions via the quiz-builder skill."""
    sys.exit(new_quiz_cmd.run(
        unit_number=unit_number,
        num_questions=num_questions,
        assessment_style=assessment_style,
        difficulty_mix=difficulty_mix,
    ))


@main.command(name="add-diagrams")
@click.option("--unit", "unit_number", default=None, type=int,
              help="Unit number to add diagrams to. Omit for an interactive prompt that defaults to all units.")
@click.option("--max-per-lesson", "max_diagrams_per_lesson", default=3, type=int,
              help="Maximum diagrams to add per lesson (default: 3).")
@click.option("--min-per-lesson", "min_diagrams_per_lesson", default=1, type=int,
              help="Minimum diagrams target per lesson; the skill may still skip a lesson if no spot earns one (default: 1).")
@click.option("--types", "allowed_types",
              default="flowchart,sequence,state,class",
              help="Comma-separated list of allowed Mermaid types.")
@click.option("--lesson-filter", "lesson_filter", default=None,
              help='Glob to limit which lessons get diagrams, e.g. "01-*.md".')
def add_diagrams(unit_number: int, max_diagrams_per_lesson: int,
                  min_diagrams_per_lesson: int, allowed_types: str,
                  lesson_filter: str):
    """Add Mermaid diagrams to existing lessons via the diagram-builder skill."""
    sys.exit(add_diagrams_cmd.run(
        unit_number=unit_number,
        max_diagrams_per_lesson=max_diagrams_per_lesson,
        min_diagrams_per_lesson=min_diagrams_per_lesson,
        allowed_types=allowed_types,
        lesson_filter=lesson_filter,
    ))


@main.command(name="build-final")
@click.option("--total", "total_questions", default=200, type=int,
              help="Total questions in the bank (default: 200).")
@click.option("--per-attempt", "questions_per_attempt", default=100, type=int,
              help="Questions sampled per attempt (default: 100).")
@click.option("--distribution", default="proportional",
              type=click.Choice(["proportional", "equal", "custom"]),
              help="How to distribute questions across units.")
@click.option("--difficulty", "difficulty_mix",
              default="30 percent easy, 50 percent medium, 20 percent hard",
              help="Difficulty mix description.")
@click.option("--style", "assessment_style", default="scenario",
              type=click.Choice(["scenario", "recall", "applied-calculation", "mixed"]),
              help="Assessment style.")
def build_final(total_questions: int, questions_per_attempt: int,
                 distribution: str, difficulty_mix: str, assessment_style: str):
    """Generate the course final assessment via final-assessment-builder."""
    sys.exit(build_final_cmd.run(
        total_questions=total_questions,
        questions_per_attempt=questions_per_attempt,
        distribution=distribution,
        difficulty_mix=difficulty_mix,
        assessment_style=assessment_style,
    ))


@main.command(name="build-course")
@click.option("--lessons-per-unit", default=4, type=int,
              help="Target lessons per unit (default: 4).")
@click.option("--words", "target_word_count", default=800, type=int,
              help="Target word count per lesson (default: 800).")
@click.option("--kc-questions", "questions_per_unit_kc", default=8, type=int,
              help="Knowledge check questions per unit (default: 8).")
@click.option("--final-questions", "total_final_questions", default=200, type=int,
              help="Total final assessment questions (default: 200).")
@click.option("--no-confirm", "confirm_each_unit", is_flag=True, default=True,
              help="Skip per-unit confirmation prompts (default: confirm each).")
def build_course(lessons_per_unit: int, target_word_count: int,
                  questions_per_unit_kc: int, total_final_questions: int,
                  confirm_each_unit: bool):
    """Build an entire course end to end (lessons + quizzes + final)."""
    sys.exit(build_course_cmd.run(
        lessons_per_unit=lessons_per_unit,
        target_word_count=target_word_count,
        questions_per_unit_kc=questions_per_unit_kc,
        total_final_questions=total_final_questions,
        confirm_each_unit=confirm_each_unit,
    ))


if __name__ == "__main__":
    main()
