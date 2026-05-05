"""Parses lesson markdown and quiz YAML into structured data ready for Canvas.

Lessons are markdown files with optional YAML frontmatter (title, order,
duration_minutes). The body becomes Canvas page HTML.

Quizzes (knowledge-checks and the course final) are YAML files with a list
of questions. Each question has an id, text, choices, explanation.

Canvas-specific notes:
- Pages are addressed by `page_url`, a slug Canvas derives from the page
  title. We pre-compute the slug locally so module-item creation can refer
  to the page without an extra round trip.
- Mermaid code fences inside lesson markdown stay as fenced code in the
  rendered HTML for now. Phase 11 does not pre-render them; that comes when
  the diagram pipeline is wired into sync. The page sync still works.
"""

import hashlib
import re
from pathlib import Path
from typing import Optional

import yaml
from markdown_it import MarkdownIt


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Lowercase, hyphenated slug from a string."""
    text = text.lower().strip()
    text = _SLUG_RE.sub("-", text).strip("-")
    return text or "untitled"


class LessonContent:
    """A parsed lesson ready to push to Canvas."""

    def __init__(self, file_path: Path, title: str, order: int,
                 body_markdown: str, body_html: str, duration_minutes: int = 0):
        self.file_path = file_path
        self.title = title
        self.order = order
        self.body_markdown = body_markdown
        self.body_html = body_html
        self.duration_minutes = duration_minutes
        self.content_hash = hashlib.sha256(body_markdown.encode("utf-8")).hexdigest()[:16]
        # Canvas's page_url is the title slug. We compute it locally so module
        # items can attach to the page without waiting for the create response.
        self.page_url = slugify(title)


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
    with file_path.open() as f:
        data = yaml.safe_load(f) or {}
    return data.get("unit", {})


def parse_knowledge_check(file_path: Path) -> Optional[QuizContent]:
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


def parse_course_description(file_path: Path) -> str:
    """Render course-description.md to HTML for the syllabus_body."""
    if not file_path.exists():
        return ""
    md = MarkdownIt("commonmark", {"html": True, "linkify": True, "typographer": False})
    return md.render(file_path.read_text(encoding="utf-8"))


def find_lessons_in_unit(unit_folder: Path) -> list[Path]:
    lessons_dir = unit_folder / "lessons"
    if not lessons_dir.exists():
        return []
    return sorted(lessons_dir.glob("*.md"))


def find_unit_folders(content_root: Path) -> list[Path]:
    if not content_root.exists():
        return []
    return sorted(p for p in content_root.glob("unit-*") if p.is_dir())
