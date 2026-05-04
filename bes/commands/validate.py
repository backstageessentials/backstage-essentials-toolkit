"""bes validate command.

Checks the current course repo for problems. Phase 2.5 stand-in for the
full course-validator skill that comes in Phase 5.

Currently checks:
  - course-config.yaml exists and parses
  - course-description.md exists and looks filled in
  - voice-guide.md exists if referenced from config
  - content/ has at least one unit folder
  - every unit folder has unit.yaml, lessons/, knowledge-check.yaml
  - every lesson has YAML frontmatter with title and order
  - every quiz that has questions: no duplicate IDs, every question has choices, exactly one or more correct answer
  - exam/course-final.yaml exists if the course is intended to have a final
"""

import re
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console

from ..helpers.config import find_course_root, load_config, ConfigError

console = Console()

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def run(strict: bool = False) -> int:
    """Run validation. Returns exit code (0 ok, 1 issues)."""
    course_root = find_course_root()
    if not course_root:
        console.print("[red]course-config.yaml not found. Are you inside a course repo?[/red]")
        return 1

    issues: list[tuple[str, str]] = []  # (level, message)

    def err(msg):
        issues.append(("error", msg))

    def warn(msg):
        issues.append(("warning", msg))

    # 1. Config check
    try:
        config = load_config(course_root)
    except ConfigError as e:
        err(f"course-config.yaml: {e}")
        _print_issues(issues, strict)
        return 1

    # 2. Course description
    desc_path = Path(config.get("description_path", "./course-description.md"))
    if not desc_path.is_absolute():
        desc_path = course_root / desc_path
    if not desc_path.exists():
        err(f"course-description.md not found at {desc_path.relative_to(course_root)}")
    else:
        text = desc_path.read_text(encoding="utf-8")
        if len(text.strip()) < 200:
            warn("course-description.md looks very short. Did you fill it in?")
        if "[Insert your sample here]" in text or "[Your Course Name]" in text:
            err("course-description.md still has unfilled template placeholders.")

    # 3. Voice guide (warning, not error, if missing)
    voice_path = Path(config.get("voice_guide_path", "./voice-guide.md"))
    if not voice_path.is_absolute():
        voice_path = course_root / voice_path
    if not voice_path.exists():
        warn("voice-guide.md not found. The lesson-drafter skill will not work without it.")

    # 4. Content folder
    content_dir = course_root / "content"
    if not content_dir.exists():
        err("content/ folder is missing.")
        _print_issues(issues, strict)
        return _exit_code(issues, strict)

    unit_folders = sorted(p for p in content_dir.glob("unit-*") if p.is_dir())
    if not unit_folders:
        err("content/ has no unit folders.")
        _print_issues(issues, strict)
        return _exit_code(issues, strict)

    # 5. Per-unit checks
    all_question_ids: set[str] = set()
    for unit_folder in unit_folders:
        unit_label = unit_folder.name

        # unit.yaml
        unit_yaml_path = unit_folder / "unit.yaml"
        if not unit_yaml_path.exists():
            err(f"{unit_label}: unit.yaml is missing.")
        else:
            try:
                with unit_yaml_path.open() as f:
                    unit_data = yaml.safe_load(f) or {}
                unit = unit_data.get("unit", {})
                if not unit.get("title"):
                    warn(f"{unit_label}: unit.yaml has no title.")
                if not unit.get("learning_outcomes"):
                    warn(f"{unit_label}: unit.yaml has no learning_outcomes.")
            except yaml.YAMLError as e:
                err(f"{unit_label}: unit.yaml does not parse: {e}")

        # lessons folder
        lessons_dir = unit_folder / "lessons"
        if not lessons_dir.exists():
            warn(f"{unit_label}: lessons/ folder is missing.")
        else:
            for lesson_path in sorted(lessons_dir.glob("*.md")):
                _validate_lesson(lesson_path, unit_label, err, warn)

        # knowledge check
        kc_path = unit_folder / "knowledge-check.yaml"
        if not kc_path.exists():
            warn(f"{unit_label}: knowledge-check.yaml is missing.")
        else:
            _validate_quiz(kc_path, unit_label, all_question_ids, err, warn)

    # 6. Course final
    final_path = course_root / "exam" / "course-final.yaml"
    if not final_path.exists():
        warn("exam/course-final.yaml is missing. The final assessment will not exist.")
    else:
        _validate_quiz(final_path, "course-final", all_question_ids, err, warn)

    _print_issues(issues, strict)
    return _exit_code(issues, strict)


def _validate_lesson(lesson_path: Path, unit_label: str,
                      err, warn):
    """Validate a single lesson markdown file."""
    text = lesson_path.read_text(encoding="utf-8")
    rel = f"{unit_label}/lessons/{lesson_path.name}"

    match = _FRONTMATTER_RE.match(text)
    if not match:
        warn(f"{rel}: no YAML frontmatter (title, order, etc.)")
        return

    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as e:
        err(f"{rel}: frontmatter does not parse: {e}")
        return

    if not meta.get("title"):
        warn(f"{rel}: frontmatter is missing title.")
    if "order" not in meta:
        warn(f"{rel}: frontmatter is missing order.")

    body = text[match.end():].strip()
    if len(body) < 50:
        warn(f"{rel}: body is very short. Did you write it?")


def _validate_quiz(quiz_path: Path, label: str,
                    all_question_ids: set, err, warn):
    """Validate a quiz YAML file (knowledge check or course final)."""
    try:
        with quiz_path.open() as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        err(f"{label}: {quiz_path.name} does not parse: {e}")
        return

    # The structure differs between knowledge-check and course-final
    quiz = data.get("quiz") or data.get("final_assessment") or {}
    questions = quiz.get("questions", [])

    if not questions:
        warn(f"{label}: {quiz_path.name} has no questions yet.")
        return

    for i, q in enumerate(questions):
        q_id = q.get("id")
        loc = f"{label}/{quiz_path.name} q{i+1}"
        if not q_id:
            err(f"{loc}: missing 'id' field.")
            continue
        if q_id in all_question_ids:
            err(f"{loc}: duplicate question id '{q_id}'.")
        all_question_ids.add(q_id)

        if not q.get("question"):
            err(f"{loc} ({q_id}): missing 'question' text.")

        choices = q.get("choices", [])
        if not choices:
            err(f"{loc} ({q_id}): no choices.")
            continue
        if len(choices) < 2:
            warn(f"{loc} ({q_id}): only {len(choices)} choice(s). Should have at least 2.")

        correct_count = sum(1 for c in choices if c.get("correct"))
        if correct_count == 0:
            err(f"{loc} ({q_id}): no choice marked correct.")
        elif correct_count > 1:
            warn(f"{loc} ({q_id}): {correct_count} choices marked correct (intentional?)")

        if not q.get("explanation"):
            warn(f"{loc} ({q_id}): no explanation.")


def _print_issues(issues: list, strict: bool):
    if not issues:
        console.print("[green]Validation passed. No issues found.[/green]")
        return

    errors = [i for i in issues if i[0] == "error"]
    warnings = [i for i in issues if i[0] == "warning"]

    if errors:
        console.print(f"\n[red]Errors ({len(errors)}):[/red]")
        for _, msg in errors:
            console.print(f"  [red]✗[/red] {msg}")

    if warnings:
        prefix = "[red]" if strict else "[yellow]"
        console.print(f"\n{prefix}Warnings ({len(warnings)}):[/{prefix.strip('[]')}]")
        for _, msg in warnings:
            mark = "[red]✗[/red]" if strict else "[yellow]⚠[/yellow]"
            console.print(f"  {mark} {msg}")


def _exit_code(issues: list, strict: bool) -> int:
    if any(i[0] == "error" for i in issues):
        return 1
    if strict and any(i[0] == "warning" for i in issues):
        return 1
    return 0
