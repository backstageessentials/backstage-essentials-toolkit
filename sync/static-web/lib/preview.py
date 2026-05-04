"""HTML preview generator for the static-web sync target.

Renders one HTML page per unit with brand styling, Mermaid CDN support, and a
collapsible knowledge check. The output mirrors the hand-built preview that
seeded this work; the hand-built version is now the rendering contract.

Usage from Python:

    from sync.static_web.lib.preview import render_unit_preview

    html = render_unit_preview(unit_folder, course_meta)
    Path("preview/unit-01-preview.html").write_text(html, encoding="utf-8")
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from html import escape as _esc
from pathlib import Path
from typing import Optional

import yaml
from markdown_it import MarkdownIt
from markdown_it.token import Token


BRAND_COLORS = {
    "brand": "#D6006C",
    "bg": "#FFFFFF",
    "text": "#0A0A0A",
    "muted_alpha": 0.65,
}


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)


@dataclass
class CourseMeta:
    course_name: str
    tagline: str = ""


@dataclass
class Lesson:
    title: str
    body_markdown: str


@dataclass
class Unit:
    number: int
    title: str
    lessons: list[Lesson]
    knowledge_check: list[dict]
    knowledge_check_title: str


# --------------------------------------------------------------------------
# Markdown -> HTML, with Mermaid blocks turned into <div class="mermaid">.
# --------------------------------------------------------------------------

def _make_md() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": True, "linkify": True, "typographer": False})
    return md


_HEADING_DEMOTION = {"h1": "h3", "h2": "h4", "h3": "h5", "h4": "h6", "h5": "h6", "h6": "h6"}

# {{microsim: filename.html height=400}} or {{microsim: TODO type=flashcards purpose="..."}}
_MICROSIM_RE = re.compile(r"\{\{microsim:\s*([^\s}]+)([^}]*)\}\}")


def _parse_microsim_attrs(attr_str: str) -> dict[str, str]:
    """Parse 'height=400 type=flashcards purpose="multi word"' into a dict."""
    attrs: dict[str, str] = {}
    pairs = re.findall(r'(\w+)=("([^"]*)"|(\S+))', attr_str)
    for key, _full, quoted, plain in pairs:
        attrs[key] = quoted if quoted else plain
    return attrs


def _expand_microsim_directives(text: str, unit_number: int) -> str:
    """Replace {{microsim: ...}} markers in the markdown with raw HTML iframes
    (or with a 'pending' badge for TODO slots).

    Iframes resolve to ``unit-NN-microsims/{filename}`` relative to the rendered
    HTML; the renderer copies the unit's ``microsims/`` folder there.
    """
    def replace(match: re.Match) -> str:
        first = match.group(1).strip()
        attrs = _parse_microsim_attrs(match.group(2))
        if first.upper() == "TODO":
            sim_type = attrs.get("type", "?")
            purpose = attrs.get("purpose", "(no purpose given)")
            return (
                '<div class="microsim-todo" style="margin: 1.2em 0; padding: 14px 18px; '
                'border: 1px dashed #D6006C; border-radius: 8px; '
                'background: rgba(214,0,108,0.04); color: rgba(10,10,10,0.65);">'
                f'<strong style="color:#D6006C;">MicroSim slot ({_esc(sim_type)}):</strong> '
                f'{_esc(purpose)} <em>(unfilled; run bes add-microsim)</em>'
                '</div>'
            )
        height = attrs.get("height", "400")
        try:
            int(height)
        except ValueError:
            height = "400"
        src = f"unit-{unit_number:02d}-microsims/{first}"
        return (
            '<div class="microsim-frame" style="margin: 1.4em 0;">'
            f'<iframe src="{_esc(src)}" '
            f'height="{_esc(height)}" width="100%" '
            'style="border: 1px solid #eaeaea; border-radius: 8px; display: block;" '
            'loading="lazy" '
            f'title="MicroSim: {_esc(first)}">'
            '</iframe>'
            '</div>'
        )
    return _MICROSIM_RE.sub(replace, text)


def _render_with_mermaid(md: MarkdownIt, text: str, demote_headings: bool = True,
                         drop_first_h1: bool = True) -> str:
    """Render markdown but convert ```mermaid fences into <div class="mermaid"> blocks.

    The default markdown-it renderer emits a fenced code block as
    <pre><code class="language-mermaid">...</code></pre>. Mermaid expects a
    div with class "mermaid" containing the diagram source. We catch the
    fence token and emit the alternative.

    Lesson bodies live under an externally-rendered <h3> for the lesson
    title and an <h2> for the unit title, so heading levels in the body
    are demoted by 2 (h1->h3, h2->h4, etc.). The leading h1 of a lesson
    body is dropped since the lesson title is already rendered.
    """
    tokens = md.parse(text)

    if drop_first_h1:
        for i, tok in enumerate(tokens):
            if tok.type == "heading_open" and tok.tag == "h1":
                # Drop the heading_open, the inline content, and heading_close
                close_idx = i + 1
                while close_idx < len(tokens) and not (
                    tokens[close_idx].type == "heading_close" and tokens[close_idx].tag == "h1"
                ):
                    close_idx += 1
                if close_idx < len(tokens):
                    tokens = tokens[:i] + tokens[close_idx + 1:]
                break

    if demote_headings:
        for tok in tokens:
            if tok.type in ("heading_open", "heading_close"):
                tok.tag = _HEADING_DEMOTION.get(tok.tag, tok.tag)

    out: list[str] = []
    for tok in tokens:
        if tok.type == "fence" and (tok.info or "").strip().lower() == "mermaid":
            out.append(f'<div class="mermaid">\n{tok.content.rstrip()}\n</div>\n')
        else:
            out.append(md.renderer.render([tok], md.options, {}))
    return "".join(out)


# --------------------------------------------------------------------------
# Course / unit loading.
# --------------------------------------------------------------------------

def _parse_lesson(file_path: Path) -> Lesson:
    text = file_path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if match:
        meta = yaml.safe_load(match.group(1)) or {}
        body = match.group(2)
    else:
        meta = {}
        body = text
    title = meta.get("title")
    if not title:
        stem = re.sub(r"^\d+-", "", file_path.stem)
        title = stem.replace("-", " ").title()
    return Lesson(title=title, body_markdown=body)


def _load_unit(unit_folder: Path) -> Unit:
    unit_yaml = unit_folder / "unit.yaml"
    unit_data = (yaml.safe_load(unit_yaml.read_text(encoding="utf-8")) or {}).get("unit", {})

    lessons_dir = unit_folder / "lessons"
    lesson_files = sorted(lessons_dir.glob("*.md")) if lessons_dir.exists() else []
    lessons = [_parse_lesson(p) for p in lesson_files]

    kc_path = unit_folder / "knowledge-check.yaml"
    kc_questions: list[dict] = []
    kc_title = f"Unit {unit_data.get('number', '?')} Knowledge Check"
    if kc_path.exists():
        kc = (yaml.safe_load(kc_path.read_text(encoding="utf-8")) or {}).get("quiz", {})
        kc_questions = kc.get("questions") or []
        if kc.get("title"):
            kc_title = kc["title"]

    return Unit(
        number=int(unit_data.get("number", 0) or 0),
        title=str(unit_data.get("title", unit_folder.name)),
        lessons=lessons,
        knowledge_check=kc_questions,
        knowledge_check_title=kc_title,
    )


def _load_course_meta(course_root: Path) -> CourseMeta:
    config = (yaml.safe_load((course_root / "course-config.yaml").read_text(encoding="utf-8")) or {})
    course = config.get("course", {})
    name = course.get("name", "Course")

    tagline = ""
    desc_path = course_root / "course-description.md"
    if desc_path.exists():
        text = desc_path.read_text(encoding="utf-8")
        for paragraph in text.split("\n\n"):
            stripped = paragraph.strip()
            if not stripped or stripped.startswith("#"):
                continue
            tagline = stripped.replace("\n", " ")
            break
    return CourseMeta(course_name=name, tagline=tagline)


# --------------------------------------------------------------------------
# Page assembly.
# --------------------------------------------------------------------------

_CSS = """\
:root {
  --brand: #D6006C;
  --bg: #FFFFFF;
  --text: #0A0A0A;
  --muted: rgba(10, 10, 10, 0.65);
  --rule: #eaeaea;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: system-ui, -apple-system, "Segoe UI", Inter, Helvetica, Arial, sans-serif;
  line-height: 1.6;
  font-size: 17px;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
.container {
  max-width: 720px;
  margin: 0 auto;
  padding: 32px 24px;
}
@media (min-width: 720px) {
  .container { padding: 48px 32px; }
}
h1, h2, h3, h4, h5, h6 {
  font-weight: 800;
  line-height: 1.25;
  margin: 1.6em 0 0.5em 0;
}
h1 {
  font-size: 2rem;
  color: var(--brand);
  border-bottom: 1px solid var(--brand);
  padding-bottom: 0.5em;
  margin-top: 0;
}
h2 {
  font-size: 1.5rem;
  color: var(--brand);
  margin-top: 2.2em;
}
h3 { font-size: 1.25rem; color: var(--text); }
h4 { font-size: 1.05rem; color: var(--text); margin-top: 1.4em; }
h5 { font-size: 1rem; color: var(--text); }
h6 { font-size: 0.95rem; color: var(--muted); }
p { margin: 0.8em 0; }
.tagline {
  font-size: 1.1rem;
  color: var(--muted);
  margin: 0.5em 0 2em 0;
}
a {
  color: var(--brand);
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 2px;
}
a:hover { text-decoration-thickness: 2px; }
ul, ol { padding-left: 1.5em; }
li { margin: 0.3em 0; }
code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  background: rgba(214, 0, 108, 0.08);
  padding: 0.1em 0.3em;
  border-radius: 3px;
  font-size: 0.92em;
}
pre {
  background: #f6f6f6;
  padding: 12px 16px;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 0.9em;
  line-height: 1.45;
  margin: 1em 0;
}
pre code {
  background: none;
  padding: 0;
  font-size: 1em;
}
blockquote {
  border-left: 3px solid var(--brand);
  margin: 1em 0;
  padding: 0.2em 1em;
  color: var(--muted);
}
.lesson {
  margin-bottom: 2.5em;
  padding-bottom: 1.5em;
  border-bottom: 1px solid var(--rule);
}
.lesson:last-of-type {
  border-bottom: none;
  margin-bottom: 1em;
}
.mermaid {
  margin: 1.5em auto;
  text-align: center;
  display: flex;
  justify-content: center;
  font-family: system-ui, -apple-system, "Segoe UI", Inter, Helvetica, Arial, sans-serif;
}
.mermaid svg {
  max-width: 100%;
  height: auto;
}
details {
  margin: 1em 0 0 0;
  padding: 0.8em 1em;
  background: rgba(214, 0, 108, 0.04);
  border-left: 3px solid var(--brand);
  border-radius: 0 4px 4px 0;
}
details summary {
  cursor: pointer;
  font-weight: 700;
  color: var(--brand);
  list-style: none;
}
details summary::-webkit-details-marker { display: none; }
details summary::before {
  content: "\\25B6 ";
  font-size: 0.8em;
  margin-right: 4px;
  display: inline-block;
}
details[open] summary::before { content: "\\25BC "; }
details > p:first-of-type { margin-top: 0.6em; }
.question { font-weight: 600; margin: 0.5em 0 0.4em 0; }
.choices { margin: 0.3em 0 0.6em 0; }
.kc-list { padding-left: 1.6em; }
.kc-list > li { margin-bottom: 1.8em; padding-left: 0.4em; }
.kc-list > li::marker { font-weight: 800; color: var(--brand); }
"""

_MERMAID_HEAD = '<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>'

_MERMAID_INIT = """\
<script>
mermaid.initialize({
  startOnLoad: true,
  theme: 'base',
  themeVariables: {
    primaryColor: '#FFFFFF',
    primaryTextColor: '#0A0A0A',
    primaryBorderColor: '#D6006C',
    lineColor: '#0A0A0A',
    tertiaryColor: '#F8F8F8',
    fontFamily: 'system-ui, -apple-system, "Segoe UI", Inter, Helvetica, Arial, sans-serif'
  }
});
</script>
"""


def _render_question(idx: int, q: dict) -> str:
    """Render a single knowledge-check question into a <li> with collapsible answer."""
    question_text = (q.get("question") or "").strip()
    choices = q.get("choices") or []

    correct_choices = [c for c in choices if c.get("correct")]
    explanation = (q.get("explanation") or "").strip()

    # Render question text and explanation as paragraphs (preserve simple line wraps)
    question_html = "<br>\n".join(_esc(line) for line in question_text.splitlines())

    choices_html_parts = [f"      <li>{_esc(c.get('text', ''))}</li>" for c in choices]
    choices_html = "\n".join(choices_html_parts)

    if correct_choices:
        correct_text = "; ".join(_esc(c.get("text", "")) for c in correct_choices)
    else:
        correct_text = "(none marked)"

    explanation_paras = []
    for para in explanation.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        explanation_paras.append(f"      <p>{_esc(para)}</p>")
    explanation_html = "\n".join(explanation_paras) if explanation_paras else ""

    return (
        "  <li>\n"
        f'    <p class="question">{question_html}</p>\n'
        f'    <ul class="choices">\n{choices_html}\n    </ul>\n'
        "    <details>\n"
        "      <summary>Show answer</summary>\n"
        f"      <p><strong>Correct answer:</strong> {correct_text}</p>\n"
        f"{explanation_html}\n"
        "    </details>\n"
        "  </li>"
    )


def render_unit_preview(unit_folder: Path, course_root: Optional[Path] = None) -> str:
    """Render one unit to a self-contained HTML page string."""
    if course_root is None:
        course_root = unit_folder.parent.parent
    course_meta = _load_course_meta(course_root)
    unit = _load_unit(unit_folder)
    md = _make_md()

    page_title = f"{course_meta.course_name}, Unit {unit.number} Preview"
    course_h1 = _esc(course_meta.course_name)
    unit_h2 = _esc(f"Unit {unit.number}: {unit.title}")
    tagline_html = (
        f'    <p class="tagline">{_esc(course_meta.tagline)}</p>\n'
        if course_meta.tagline else ""
    )

    lesson_sections: list[str] = []
    for lesson in unit.lessons:
        expanded = _expand_microsim_directives(lesson.body_markdown, unit.number)
        body_html = _render_with_mermaid(md, expanded)
        lesson_sections.append(
            '<section class="lesson">\n'
            f"  <h3>{_esc(lesson.title)}</h3>\n"
            f"{body_html}"
            "</section>"
        )
    lessons_block = "\n\n".join(lesson_sections) if lesson_sections else (
        "<p><em>No lessons drafted yet.</em></p>"
    )

    if unit.knowledge_check:
        kc_items = "\n".join(
            _render_question(i, q) for i, q in enumerate(unit.knowledge_check)
        )
        kc_block = (
            f"    <h2>{_esc(unit.knowledge_check_title)}</h2>\n\n"
            f'    <ol class="kc-list">\n{kc_items}\n</ol>'
        )
    else:
        kc_block = (
            f"    <h2>{_esc(unit.knowledge_check_title)}</h2>\n"
            "    <p><em>No knowledge check questions yet.</em></p>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(page_title)}</title>
  <style>
{_CSS}</style>
  {_MERMAID_HEAD}
</head>
<body>
  <div class="container">
    <h1>{course_h1}</h1>
    <h2>{unit_h2}</h2>
{tagline_html}
    <h2>Lessons</h2>

{lessons_block}

{kc_block}

  </div>
  {_MERMAID_INIT}
</body>
</html>
"""


def render_all_units(course_root: Path, output_dir: Path,
                     units: Optional[list[int]] = None) -> list[Path]:
    """Render every unit (or the filtered subset) and write the HTML files.

    Returns the list of paths written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    content_root = course_root / "content"
    if not content_root.exists():
        return written

    for unit_folder in sorted(content_root.glob("unit-*")):
        if not unit_folder.is_dir():
            continue
        unit_yaml = unit_folder / "unit.yaml"
        if not unit_yaml.exists():
            continue
        meta = (yaml.safe_load(unit_yaml.read_text(encoding="utf-8")) or {}).get("unit", {})
        n = int(meta.get("number", 0) or 0)
        if units and n not in units:
            continue
        html = render_unit_preview(unit_folder, course_root=course_root)
        out_path = output_dir / f"unit-{n:02d}-preview.html"
        out_path.write_text(html, encoding="utf-8")
        written.append(out_path)

        # Copy this unit's microsims folder alongside the rendered HTML so
        # iframe src="unit-NN-microsims/foo.html" resolves.
        microsims_src = unit_folder / "microsims"
        if microsims_src.exists() and microsims_src.is_dir():
            microsims_dst = output_dir / f"unit-{n:02d}-microsims"
            if microsims_dst.exists():
                shutil.rmtree(microsims_dst)
            shutil.copytree(microsims_src, microsims_dst)

    return written
