"""bes new-course command.

Bootstraps a new course repo by orchestrating course-spec-builder and
repo-bootstrap skills. Drops a course specific CLAUDE.md immediately so
any Claude Code instance opened in the new folder learns how to drive
the toolkit, even before the rest of the scaffolding is filled in. The
remaining work (build spec, repo bootstrap, voice guide stub) is
described in the structured prompt this command prints; Claude Code
runs it.
"""

import sys
from pathlib import Path

import click
from rich.console import Console

console = Console()


_TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "skills"
    / "repo-bootstrap"
    / "templates"
    / "course-claude.template.md"
)


def run(course_name: str = None, target_platform: str = None,
        unit_count: int = 6, output_path: str = None,
        target_audience: str = None) -> int:
    """Run new-course command. Returns exit code."""
    if output_path is None:
        output_path = "."
    output_path = Path(output_path).resolve()

    if not course_name:
        course_name = click.prompt("Course name", type=str)
    if not target_platform:
        target_platform = click.prompt(
            "Target platform",
            type=click.Choice(["thinkific", "canvas", "google-classroom",
                              "static-web", "pdf"]),
            default="thinkific",
        )
    if not target_audience:
        target_audience = click.prompt(
            "Target audience (one short sentence)",
            type=str,
            default="To be filled in from course-description.md.",
        )

    default_slug = course_name.lower().replace(" ", "-")
    course_slug = click.prompt("Course slug", type=str, default=default_slug)

    target = output_path / course_slug
    if target.exists() and any(target.iterdir()):
        if not click.confirm(
            f"{target} exists and is not empty. Continue anyway?",
            default=False,
        ):
            console.print("[yellow]Cancelled.[/yellow]")
            return 0

    target.mkdir(parents=True, exist_ok=True)

    claude_md_path = _write_course_claude_md(
        target=target,
        course_name=course_name,
        course_slug=course_slug,
        target_platform=target_platform,
        target_audience=target_audience,
    )

    prompt = _build_new_course_prompt(
        course_name=course_name,
        course_slug=course_slug,
        target_platform=target_platform,
        unit_count=unit_count,
        target_path=target,
    )

    console.print()
    console.print(f"[green]Course folder created:[/green] {target}")
    if claude_md_path is not None:
        console.print(f"[green]Course CLAUDE.md written:[/green] {claude_md_path}")
    console.print()
    console.print("[cyan]Next: paste this prompt into Claude Code[/cyan]")
    console.print(f"[cyan](in the {target} folder, type 'claude' first):[/cyan]")
    console.print()
    console.print("=" * 70)
    console.print(prompt, markup=False, highlight=False)
    console.print("=" * 70)
    console.print()
    console.print("[yellow]After Claude Code finishes, review the generated files,[/yellow]")
    console.print("[yellow]then fill in course-description.md and voice-guide.md before[/yellow]")
    console.print("[yellow]running other bes commands.[/yellow]")

    return 0


def _write_course_claude_md(target: Path, course_name: str, course_slug: str,
                             target_platform: str, target_audience: str) -> Path:
    """Render the course CLAUDE.md template and write it to target/CLAUDE.md.

    Returns the written path. Returns None if the template is missing
    (in which case we print a warning and let the rest of the bootstrap
    continue).
    """
    if not _TEMPLATE_PATH.exists():
        console.print(
            f"[yellow]Template missing at {_TEMPLATE_PATH}; "
            "skipping CLAUDE.md drop.[/yellow]"
        )
        return None
    template = _TEMPLATE_PATH.read_text(encoding="utf-8")
    rendered = (
        template
        .replace("{COURSE_NAME}", course_name)
        .replace("{COURSE_SLUG}", course_slug)
        .replace("{TARGET_PLATFORM}", target_platform)
        .replace("{TARGET_AUDIENCE}", target_audience)
    )
    out = target / "CLAUDE.md"
    out.write_text(rendered, encoding="utf-8")
    return out


def _build_new_course_prompt(course_name: str, course_slug: str,
                              target_platform: str, unit_count: int,
                              target_path: Path) -> str:
    """Build the prompt for Claude Code to bootstrap the course."""
    return f"""I want to create a new course using the toolkit. Run the course-spec-builder \
and repo-bootstrap skills in sequence to scaffold it. The new-course command has already \
created the target folder and dropped a course CLAUDE.md; do not overwrite that file.

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
content/ folder with {unit_count} unit subfolders, exam/, scripts/, etc.). Do not write or \
overwrite CLAUDE.md; new-course already wrote it.

3. Create empty placeholder course-description.md and voice-guide.md at the course root, \
with template content from docs/course-description-guide.md and docs/voice-guide-template.md \
in the toolkit.

4. After scaffolding, show me what was created and remind me to:
   - Fill in course-description.md before running any other skill
   - Fill in voice-guide.md before running lesson-drafter
   - Initialize git and push to a new GitHub repo when ready

Do not write actual lesson or quiz content yet. That is for later steps."""
