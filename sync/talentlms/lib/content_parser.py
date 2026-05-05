"""Parses lesson markdown and quiz YAML into structured data ready for the API.

Mirrors sync/thinkific/lib/content_parser.py and sync/canvas/lib/content_parser.py
so the same course YAML works against any of the three sync targets.
"""

import hashlib
import re
from pathlib import Path
from typing import Optional

import yaml
from markdown_it import MarkdownIt


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)


class LessonContent:
    """A parsed lesson ready to push to TalentLMS."""

    def __init__(self, file_path: Path, title: str, order: int,
                 body_markdown: str, body_html: str,
                 duration_minutes: int = 0):
        self.file_path = file_path
        self.title = title
        self.order = order
        self.body_markdown = body_markdown
        self.body_html = body_html
        self.duration_minutes = duration_minutes
        self.content_hash = hashlib.sha256(
            body_markdown.encode("utf-8")
        ).hexdigest()[:16]


class QuizContent:
    """A parsed quiz (knowledge check or course final) ready to push."""

    def __init__(self, file_path: Path, title: str, pass_threshold: float,
                 questions: list[dict], max_attempts: Optional[int] = None,
                 randomize: bool = True):
        self.file_path = file_path
        self.title = title
        self.pass_threshold = pass_threshold
        self.questions = questions
        self.max_attempts = max_attempts
        self.randomize = randomize
        self.content_hash = hashlib.sha256(
            yaml.dump(questions, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]


def _parse_frontmatter(text: str) -> tuple[dict, str]:
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

    title = metadata.get("title")
    if not title:
        stem = file_path.stem
        stem = re.sub(r"^\d+-", "", stem)
        title = stem.replace("-", " ").title()

    order = metadata.get("order", 0)
    duration = metadata.get("duration_minutes", 0)

    md = MarkdownIt("commonmark", {"html": True, "linkify": True,
                                    "typographer": False})
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


def parse_course_description(file_path: Path) -> str:
    """Read course-description.md and render it to HTML.

    Used as the description body when creating the TalentLMS course.
    """
    if not file_path.exists():
        return ""
    text = file_path.read_text(encoding="utf-8")
    metadata, body = _parse_frontmatter(text)
    md = MarkdownIt("commonmark", {"html": True, "linkify": True,
                                    "typographer": False})
    return md.render(body or text)


def parse_knowledge_check(file_path: Path) -> Optional[QuizContent]:
    """Parse a knowledge-check.yaml file. Returns None if no questions yet."""
    with file_path.open() as f:
        data = yaml.safe_load(f) or {}
    quiz = data.get("quiz", {})
    questions = quiz.get("questions", [])
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
    max_attempts_raw = final.get("max_attempts")
    try:
        max_attempts = int(max_attempts_raw) if max_attempts_raw is not None else None
    except (TypeError, ValueError):
        max_attempts = None
    randomize = bool(final.get("randomize", True))
    return QuizContent(
        file_path=file_path,
        title=final.get("name", "Course Final"),
        pass_threshold=final.get("pass_threshold", 0.75),
        questions=questions,
        max_attempts=max_attempts,
        randomize=randomize,
    )


def find_lessons_in_unit(unit_folder: Path) -> list[Path]:
    """Find all lesson markdown files in a unit's lessons/ folder."""
    lessons_dir = unit_folder / "lessons"
    if not lessons_dir.exists():
        return []
    return sorted(lessons_dir.glob("*.md"))


def find_unit_folders(content_root: Path) -> list[Path]:
    """Find all unit folders in content/."""
    if not content_root.exists():
        return []
    return sorted(p for p in content_root.glob("unit-*") if p.is_dir())
