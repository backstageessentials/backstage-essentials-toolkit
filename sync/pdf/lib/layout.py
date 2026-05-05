"""Builds the HTML document that the PDF renderer turns into a PDF.

The pipeline is markdown -> expanded HTML (diagrams + microsims rendered
or stubbed) -> a single self-contained HTML string with the brand CSS
inline. Both WeasyPrint and the Chrome-headless fallback consume the
same string.

Sections, in order:
1. Cover page (`<section class="cover">`)
2. Table of contents (`<section class="toc">`)
3. Course description page (`<section class="course-description">`)
4. One `<section class="unit">` per unit, each containing lessons,
   embedded diagrams, MicroSims, and a study-format knowledge check.
5. Optional course final (`<section class="final-section">`) when
   `pdf_include_final` is true in course-config.yaml.

All cross-page references use anchor links so WeasyPrint's
target-counter() can resolve TOC page numbers without a second pass.
"""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass
from html import escape as _esc
from pathlib import Path
from typing import Optional

import yaml
from markdown_it import MarkdownIt

from .diagram_handler import expand_mermaid_blocks
from .microsim_handler import expand_microsim_directives


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)


_HEADING_DEMOTION = {"h1": "h3", "h2": "h4", "h3": "h5", "h4": "h6", "h5": "h6", "h6": "h6"}


@dataclass
class CourseInfo:
    name: str
    slug: str
    audience: str
    version: str
    author: str
    copyright_holder: str
    copyright_year: str
    description_html: str
    page_size: str  # "Letter" or "A4"
    microsim_strategy: str  # "qr" or "screenshot"
    microsim_base_url: Optional[str]
    include_final: bool


@dataclass
class Lesson:
    title: str
    body_markdown: str
    duration_minutes: int


@dataclass
class Unit:
    number: int
    title: str
    description: str
    learning_outcomes: list[str]
    lessons: list[Lesson]
    knowledge_check_title: str
    knowledge_check_questions: list[dict]


# ----- Loading helpers -----

def _make_md() -> MarkdownIt:
    return MarkdownIt("commonmark", {"html": True, "linkify": True, "typographer": False})


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    metadata = yaml.safe_load(match.group(1)) or {}
    body = match.group(2)
    return metadata, body


def _parse_lesson_file(path: Path) -> Lesson:
    text = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)
    title = meta.get("title")
    if not title:
        stem = re.sub(r"^\d+-", "", path.stem)
        title = stem.replace("-", " ").title()
    return Lesson(
        title=title,
        body_markdown=body,
        duration_minutes=int(meta.get("duration_minutes", 0) or 0),
    )


def _load_unit(unit_folder: Path) -> Unit:
    unit_yaml = unit_folder / "unit.yaml"
    data = (yaml.safe_load(unit_yaml.read_text(encoding="utf-8")) or {}).get("unit", {})

    lessons_dir = unit_folder / "lessons"
    lesson_paths = sorted(lessons_dir.glob("*.md")) if lessons_dir.exists() else []
    lessons = [_parse_lesson_file(p) for p in lesson_paths]

    kc_path = unit_folder / "knowledge-check.yaml"
    kc_questions: list[dict] = []
    kc_title = f"Unit {data.get('number', '?')} Knowledge Check"
    if kc_path.exists():
        kc = (yaml.safe_load(kc_path.read_text(encoding="utf-8")) or {}).get("quiz", {})
        kc_questions = kc.get("questions") or []
        if kc.get("title"):
            kc_title = kc["title"]

    return Unit(
        number=int(data.get("number", 0) or 0),
        title=str(data.get("title", unit_folder.name)),
        description=str(data.get("description", "") or ""),
        learning_outcomes=list(data.get("learning_outcomes") or []),
        lessons=lessons,
        knowledge_check_title=kc_title,
        knowledge_check_questions=kc_questions,
    )


def gather_units(course_root: Path) -> list[Unit]:
    content_root = course_root / "content"
    if not content_root.exists():
        return []
    units = []
    for folder in sorted(content_root.glob("unit-*")):
        if not folder.is_dir():
            continue
        if not (folder / "unit.yaml").exists():
            continue
        units.append(_load_unit(folder))
    return units


def load_course_info(course_root: Path) -> CourseInfo:
    config = (
        yaml.safe_load((course_root / "course-config.yaml").read_text(encoding="utf-8")) or {}
    )
    course = config.get("course", {})
    name = course.get("name", "Course")
    slug = course.get("slug", "course")
    page_size = (course.get("pdf_page_size") or "letter").lower()
    page_size_canonical = "A4" if page_size == "a4" else "Letter"
    strategy = (course.get("pdf_microsim_strategy") or "qr").lower()
    if strategy not in ("qr", "screenshot"):
        strategy = "qr"
    base_url = course.get("pdf_microsim_base_url")
    include_final = bool(course.get("pdf_include_final", False))
    author = course.get("author") or course.get("copyright_holder") or "Backstage Essentials"
    version = str(course.get("version") or course.get("course_version") or "1.0")
    audience = ""
    desc_path = Path(course.get("description_path", "./course-description.md"))
    if not desc_path.is_absolute():
        desc_path = course_root / desc_path
    description_html = ""
    if desc_path.exists():
        md = _make_md()
        description_html = md.render(desc_path.read_text(encoding="utf-8"))
        # Pull the first non-heading paragraph as the audience tagline.
        for para in desc_path.read_text(encoding="utf-8").split("\n\n"):
            stripped = para.strip()
            if stripped and not stripped.startswith("#"):
                audience = stripped.replace("\n", " ")
                break

    return CourseInfo(
        name=name,
        slug=slug,
        audience=audience,
        version=version,
        author=author,
        copyright_holder=course.get("copyright_holder") or author,
        copyright_year=str(course.get("copyright_year") or _dt.date.today().year),
        description_html=description_html,
        page_size=page_size_canonical,
        microsim_strategy=strategy,
        microsim_base_url=base_url,
        include_final=include_final,
    )


def load_course_final(course_root: Path) -> Optional[dict]:
    path = course_root / "exam" / "course-final.yaml"
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("final_assessment")


# ----- Rendering helpers -----

def _render_with_demoted_headings(md: MarkdownIt, text: str,
                                    drop_first_h1: bool = True,
                                    demote: bool = True) -> str:
    """Render markdown but skip the leading h1 (since the lesson title is
    already an h3 above the body) and demote remaining headings two levels."""
    tokens = md.parse(text)

    if drop_first_h1:
        for i, tok in enumerate(tokens):
            if tok.type == "heading_open" and tok.tag == "h1":
                close_idx = i + 1
                while close_idx < len(tokens) and not (
                    tokens[close_idx].type == "heading_close"
                    and tokens[close_idx].tag == "h1"
                ):
                    close_idx += 1
                if close_idx < len(tokens):
                    tokens = tokens[: i] + tokens[close_idx + 1:]
                break

    if demote:
        for tok in tokens:
            if tok.type in ("heading_open", "heading_close"):
                tok.tag = _HEADING_DEMOTION.get(tok.tag, tok.tag)

    return md.renderer.render(tokens, md.options, {})


def _render_lesson(md: MarkdownIt, lesson: Lesson, unit_number: int,
                    course: CourseInfo, mermaid_cache: Path,
                    screenshot_dir: Optional[Path]) -> str:
    """Render one lesson as a `<section class="lesson">` block."""
    body = lesson.body_markdown
    body = expand_microsim_directives(
        body,
        unit_number=unit_number,
        strategy=course.microsim_strategy,
        base_url=course.microsim_base_url,
        screenshot_dir=screenshot_dir,
    )
    body = expand_mermaid_blocks(body, cache_dir=mermaid_cache)
    body_html = _render_with_demoted_headings(md, body)

    duration_html = ""
    if lesson.duration_minutes:
        duration_html = (
            f'<p class="lesson-meta">Estimated reading time: '
            f'{lesson.duration_minutes} minutes</p>'
        )

    return (
        '<section class="lesson">\n'
        f'  <h3>{_esc(lesson.title)}</h3>\n'
        f'  {duration_html}\n'
        f'  {body_html}\n'
        '</section>'
    )


def _render_kc_question(idx: int, q: dict) -> str:
    """Render one knowledge-check question in study format.

    Question and choices first, then a styled "Answer" block with the
    correct choice and explanation. The block is on the same page as the
    question whenever possible (page-break-inside: avoid is set in CSS).
    """
    question_text = (q.get("question") or "").strip()
    choices = q.get("choices") or []
    correct = [c for c in choices if c.get("correct")]
    explanation = (q.get("explanation") or "").strip()

    question_html = "<br>\n".join(_esc(line) for line in question_text.splitlines())
    choices_html = "\n".join(
        f"      <li>{_esc(c.get('text', ''))}</li>" for c in choices
    )
    if correct:
        correct_text = "; ".join(_esc(c.get("text", "")) for c in correct)
    else:
        correct_text = "(none marked)"

    explanation_html = ""
    if explanation:
        paras = []
        for para in explanation.split("\n\n"):
            para = para.strip()
            if para:
                paras.append(f"<p>{_esc(para)}</p>")
        explanation_html = "\n".join(paras)

    return (
        '  <li>\n'
        f'    <p class="kc-question">{question_html}</p>\n'
        f'    <ol class="kc-choices">\n{choices_html}\n    </ol>\n'
        '    <div class="kc-answer">\n'
        f'      <p><span class="kc-answer-label">Answer:</span> {correct_text}</p>\n'
        f'      {explanation_html}\n'
        '    </div>\n'
        '  </li>'
    )


def _render_unit(md: MarkdownIt, unit: Unit, course: CourseInfo,
                  mermaid_cache: Path, screenshot_dir: Optional[Path]) -> str:
    outcomes_html = ""
    if unit.learning_outcomes:
        items = "\n".join(f"      <li>{_esc(o)}</li>" for o in unit.learning_outcomes)
        outcomes_html = (
            '  <div class="unit-outcomes">\n'
            '    <h3>Learning outcomes</h3>\n'
            f'    <ul>\n{items}\n    </ul>\n'
            '  </div>'
        )

    description_html = ""
    if unit.description.strip():
        description_html = f'  <p class="unit-description">{_esc(unit.description)}</p>'

    lessons_html = "\n".join(
        _render_lesson(md, lesson, unit.number, course, mermaid_cache, screenshot_dir)
        for lesson in unit.lessons
    ) or '  <p><em>Lessons coming soon.</em></p>'

    kc_html = ""
    if unit.knowledge_check_questions:
        items = "\n".join(
            _render_kc_question(i, q)
            for i, q in enumerate(unit.knowledge_check_questions)
        )
        kc_html = (
            '<section class="kc-section">\n'
            f'  <h2>{_esc(unit.knowledge_check_title)}</h2>\n'
            '  <p><em>Try each question first, then read the answer block. '
            'These knowledge checks are open-book and ungraded.</em></p>\n'
            f'  <ol class="kc-list">\n{items}\n  </ol>\n'
            '</section>'
        )

    unit_id = f"unit-{unit.number}"
    return (
        f'<section class="unit" id="{unit_id}">\n'
        '  <header class="unit-header">\n'
        f'    <p class="unit-eyebrow">Unit {unit.number}</p>\n'
        f'    <h1>{_esc(unit.title)}</h1>\n'
        '  </header>\n'
        f'{description_html}\n'
        f'{outcomes_html}\n'
        f'{lessons_html}\n'
        f'{kc_html}\n'
        '</section>'
    )


def _render_cover(course: CourseInfo) -> str:
    today = _dt.date.today().isoformat()
    audience_html = (
        f'<p class="cover-subtitle">{_esc(course.audience)}</p>'
        if course.audience else ""
    )
    return (
        '<section class="cover">\n'
        '  <p class="cover-eyebrow">Course Workbook</p>\n'
        f'  <h1 class="cover-title">{_esc(course.name)}</h1>\n'
        f'  {audience_html}\n'
        '  <hr class="cover-rule">\n'
        '  <div class="cover-metadata">\n'
        f'    <strong>Author:</strong> {_esc(course.author)}<br>\n'
        f'    <strong>Version:</strong> {_esc(course.version)}<br>\n'
        f'    <strong>Generated:</strong> {today}<br>\n'
        f'    <strong>Copyright:</strong> © {_esc(course.copyright_year)} '
        f'{_esc(course.copyright_holder)}\n'
        '  </div>\n'
        '</section>'
    )


def _render_toc(units: list[Unit], include_final: bool) -> str:
    rows: list[str] = []
    for unit in units:
        rows.append(
            f'  <li class="toc-unit">\n'
            f'    <div class="toc-row">\n'
            f'      <a class="toc-link" href="#unit-{unit.number}">'
            f'Unit {unit.number}: {_esc(unit.title)}</a>\n'
            f'      <span class="toc-leader"></span>\n'
            f'      <span class="toc-page"></span>\n'
            f'    </div>\n'
            f'  </li>'
        )
        for i, lesson in enumerate(unit.lessons, 1):
            rows.append(
                f'  <li class="toc-lesson">\n'
                f'    <div class="toc-row">\n'
                f'      <span>{unit.number}.{i} {_esc(lesson.title)}</span>\n'
                f'      <span class="toc-leader"></span>\n'
                f'      <span class="toc-page"></span>\n'
                f'    </div>\n'
                f'  </li>'
            )
    if include_final:
        rows.append(
            '  <li class="toc-unit">\n'
            '    <div class="toc-row">\n'
            '      <a class="toc-link" href="#course-final">Course Final Assessment</a>\n'
            '      <span class="toc-leader"></span>\n'
            '      <span class="toc-page"></span>\n'
            '    </div>\n'
            '  </li>'
        )
    rows_html = "\n".join(rows)
    return (
        '<section class="toc" id="toc">\n'
        '  <h1>Contents</h1>\n'
        f'  <ul>\n{rows_html}\n  </ul>\n'
        '</section>'
    )


def _render_course_description(course: CourseInfo) -> str:
    if not course.description_html:
        return ""
    return (
        '<section class="course-description">\n'
        '  <h1>About this course</h1>\n'
        f'  {course.description_html}\n'
        '</section>'
    )


def _render_final(final: Optional[dict]) -> str:
    if final is None:
        return ""
    questions = final.get("questions") or []
    name = final.get("name") or "Course Final Assessment"
    if not questions:
        body = '<p><em>No questions in the final assessment yet.</em></p>'
    else:
        items = "\n".join(_render_kc_question(i, q) for i, q in enumerate(questions))
        body = f'<ol class="kc-list">\n{items}\n</ol>'
    return (
        '<section class="final-section" id="course-final">\n'
        f'  <h1>{_esc(name)}</h1>\n'
        '  <p><em>The final assessment is included for reference. Take it in '
        'a controlled environment, not as a study aid.</em></p>\n'
        f'  {body}\n'
        '</section>'
    )


def build_html_document(course_root: Path, mermaid_cache: Path,
                          screenshot_dir: Optional[Path] = None) -> tuple[str, CourseInfo]:
    """Assemble the full HTML document for the PDF.

    Returns (html_string, course_info). The course_info is also used by
    the renderer to set the page footer variables.
    """
    course = load_course_info(course_root)
    units = gather_units(course_root)
    final = load_course_final(course_root) if course.include_final else None

    md = _make_md()
    style_css = (Path(__file__).parent / "style.css").read_text(encoding="utf-8")
    style_css = (
        style_css
        .replace("__PAGE_SIZE__", course.page_size)
        .replace("__COURSE_TITLE__", _css_string_safe(course.name))
        .replace("__COPYRIGHT_YEAR__", _css_string_safe(course.copyright_year))
        .replace("__COPYRIGHT_HOLDER__", _css_string_safe(course.copyright_holder))
    )

    cover_html = _render_cover(course)
    toc_html = _render_toc(units, include_final=course.include_final and final is not None)
    desc_html = _render_course_description(course)
    units_html = "\n".join(
        _render_unit(md, u, course, mermaid_cache, screenshot_dir) for u in units
    )
    final_html = _render_final(final) if course.include_final else ""

    title = _esc(course.name)
    body = f"{cover_html}\n{toc_html}\n{desc_html}\n{units_html}\n{final_html}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
{style_css}
  </style>
</head>
<body>
{body}
</body>
</html>
""", course


def _css_string_safe(value: str) -> str:
    """Escape a string for use inside a CSS string literal."""
    return value.replace("\\", "\\\\").replace('"', '\\"')
