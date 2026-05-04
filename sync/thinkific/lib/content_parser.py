"""Parses lesson markdown and quiz YAML into structured data ready for the API.

Lessons are markdown files with optional YAML frontmatter. The frontmatter
holds title, order, type, duration_minutes. The body is the lesson content,
which we convert to HTML for Thinkific.

Quizzes (knowledge-checks and the course final) are YAML files with a list
of questions. Each question has an id, text, choices, and explanation.
"""

import hashlib
import re
from pathlib import Path
from typing import Optional

import yaml
from markdown_it import MarkdownIt


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)


class LessonContent:
    """A parsed lesson ready to push to Thinkific."""

    def __init__(self, file_path: Path, title: str, order: int,
                 body_markdown: str, body_html: str, duration_minutes: int = 0):
        self.file_path = file_path
        self.title = title
        self.order = order
        self.body_markdown = body_markdown
        self.body_html = body_html
        self.duration_minutes = duration_minutes
        self.content_hash = hashlib.sha256(body_markdown.encode("utf-8")).hexdigest()[:16]


class QuizContent:
    """A parsed quiz (knowledge check or course final) ready to push."""

    def __init__(self, file_path: Path, title: str, pass_threshold: float,
                 questions: list[dict]):
        self.file_path = file_path
        self.title = title
        self.pass_threshold = pass_threshold
        self.questions = questions
        # Hash of all question text for change detection
        self.content_hash = hashlib.sha256(
            yaml.dump(questions, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter from a markdown file. Returns (metadata, body)."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    metadata = yaml.safe_load(match.group(1)) or {}
    body = match.group(2)
    return metadata, body


def parse_lesson(file_path: Path) -> LessonContent:
    """Parse a lesson markdown file into LessonContent."""
    text = file_path.read_text(encoding="utf-8")
    metadata, body = _parse_frontmatter(text)

    # Default title from filename if not in frontmatter
    title = metadata.get("title")
    if not title:
        # Strip leading number prefix like "01-" and convert hyphens to spaces
        stem = file_path.stem
        stem = re.sub(r"^\d+-", "", stem)
        title = stem.replace("-", " ").title()

    order = metadata.get("order", 0)
    duration = metadata.get("duration_minutes", 0)

    # Convert markdown body to HTML
    md = MarkdownIt("commonmark", {"html": True, "linkify": True, "typographer": False})
    body_html = md.render(body)

    return LessonContent(
        file_path=file_path,
        title=title,
        order=order,
        body_markdown=body,
        body_html=body_html,
        duration_minutes=duration,
    )


def parse_unit_yaml(file_path: Path) -> dict:
    """Parse a unit.yaml file. Returns the unit dict."""
    with file_path.open() as f:
        data = yaml.safe_load(f) or {}
    return data.get("unit", {})


def parse_knowledge_check(file_path: Path) -> Optional[QuizContent]:
    """Parse a knowledge-check.yaml file. Returns None if no questions yet."""
    with file_path.open() as f:
        data = yaml.safe_load(f) or {}
    quiz = data.get("quiz", {})
    questions = quiz.get("questions", [])

    # Skip empty quizzes (placeholders that haven't been filled in yet)
    if not questions:
        return None

    return QuizContent(
        file_path=file_path,
        title=quiz.get("title", file_path.stem),
        pass_threshold=quiz.get("pass_threshold", 0.7),
        questions=questions,
    )


def parse_course_final(file_path: Path) -> Optional[QuizContent]:
    """Parse the course-final.yaml file. Returns None if no questions yet."""
    with file_path.open() as f:
        data = yaml.safe_load(f) or {}
    final = data.get("final_assessment", {})
    questions = final.get("questions", [])

    if not questions:
        return None

    return QuizContent(
        file_path=file_path,
        title=final.get("name", "Course Final"),
        pass_threshold=final.get("pass_threshold", 0.75),
        questions=questions,
    )


def find_lessons_in_unit(unit_folder: Path) -> list[Path]:
    """Find all lesson markdown files in a unit's lessons/ folder, sorted by name."""
    lessons_dir = unit_folder / "lessons"
    if not lessons_dir.exists():
        return []
    return sorted(lessons_dir.glob("*.md"))


def find_unit_folders(content_root: Path) -> list[Path]:
    """Find all unit folders in content/, sorted by name."""
    if not content_root.exists():
        return []
    return sorted(p for p in content_root.glob("unit-*") if p.is_dir())
