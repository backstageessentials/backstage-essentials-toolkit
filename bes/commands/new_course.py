"""bes new-course command.

Bootstraps a new course repo by orchestrating course-spec-builder and
repo-bootstrap skills. Outputs a structured prompt the user pastes into
Claude Code to do the actual work.

Why prompts instead of direct execution: the skills do creative writing
(course descriptions, learning outcomes, etc.) that needs an LLM. bes
itself does not call LLM APIs; Claude Code does. So bes prepares the
context and the prompt, the user runs Claude Code with that prompt.
"""

import sys
from pathlib import Path

import click
from rich.console import Console

console = Console()


def run(course_name: str = None, target_platform: str = None,
        unit_count: int = 6, output_path: str = None) -> int:
    """Run new-course command. Returns exit code."""
    if output_path is None:
        output_path = "."
    output_path = Path(output_path).resolve()

    # If we are not given a course name, prompt
    if not course_name:
        course_name = click.prompt("Course name", type=str)
    if not target_platform:
        target_platform = click.prompt(
            "Target platform",
            type=click.Choice(["thinkific", "canvas", "google-classroom",
                              "static-web", "pdf"]),
            default="thinkific",
        )

    # Slug derived from course name unless user wants to override
    default_slug = course_name.lower().replace(" ", "-")
    course_slug = click.prompt("Course slug", type=str, default=default_slug)

    # Verify the target folder is empty or new
    target = output_path / course_slug
    if target.exists() and any(target.iterdir()):
        if not click.confirm(
            f"{target} exists and is not empty. Continue anyway?",
            default=False,
        ):
            console.print("[yellow]Cancelled.[/yellow]")
            return 0

    target.mkdir(parents=True, exist_ok=True)

    # Generate the prompt for Claude Code
    prompt = _build_new_course_prompt(
        course_name=course_name,
        course_slug=course_slug,
        target_platform=target_platform,
        unit_count=unit_count,
        target_path=target,
    )

    console.print()
    console.print(f"[green]Course folder created:[/green] {target}")
    console.print()
    console.print("[cyan]Next: paste this prompt into Claude Code[/cyan]")
    console.print(f"[cyan](in the {target} folder, type 'claude' first):[/cyan]")
    console.print()
    console.print("=" * 70)
    console.print(prompt)
    console.print("=" * 70)
    console.print()
    console.print("[yellow]After Claude Code finishes, review the generated files,[/yellow]")
    console.print("[yellow]then fill in course-description.md and voice-guide.md before[/yellow]")
    console.print("[yellow]running other bes commands.[/yellow]")

    return 0


def _build_new_course_prompt(course_name: str, course_slug: str,
                              target_platform: str, unit_count: int,
                              target_path: Path) -> str:
    """Build the prompt for Claude Code to bootstrap the course."""
    return f"""I want to create a new course using the toolkit. Run the course-spec-builder \
and repo-bootstrap skills in sequence to scaffold it.

Inputs:
- course_name: "{course_name}"
- course_slug: "{course_slug}"
- target_platform: {target_platform}
- unit_count: {unit_count}
- target_path: {target_path}

Steps:
1. Read the course-spec-builder SKILL.md from the toolkit and follow it to generate \
docs/build-spec.md and docs/build-spec-source/build-spec.docx in the course folder.

2. Read the repo-bootstrap SKILL.md from the toolkit and follow it to scaffold the \
folder structure (course-config.yaml, .gitignore, .env.example, requirements.txt, README.md, \
content/ folder with {unit_count} unit subfolders, exam/, scripts/, etc.).

3. Create empty placeholder course-description.md and voice-guide.md at the course root, \
with template content from docs/course-description-guide.md and docs/voice-guide-template.md \
in the toolkit.

4. After scaffolding, show me what was created and remind me to:
   - Fill in course-description.md before running any other skill
   - Fill in voice-guide.md before running lesson-drafter
   - Initialize git and push to a new GitHub repo when ready

Do not write actual lesson or quiz content yet. That is for later steps."""
