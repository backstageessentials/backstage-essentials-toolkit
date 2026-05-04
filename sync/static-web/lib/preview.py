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

/* Test mode (course final): interactive form with radios, score, reveal. */
.test-section {
  margin-top: 2em;
  padding-top: 1.4em;
  border-top: 2px solid var(--brand);
}
.test-meta {
  font-size: 0.92rem; color: var(--muted);
  background: rgba(214, 0, 108, 0.04);
  border-radius: 6px; padding: 10px 14px; margin: 0 0 1em 0;
}
.test-progress {
  position: sticky; top: 0; z-index: 5;
  background: var(--bg);
  padding: 10px 14px; margin: 0 0 1em 0;
  border: 1px solid var(--brand); border-radius: 6px;
  font-weight: 700; color: var(--brand);
  display: flex; justify-content: space-between; align-items: center;
}
.test-question {
  margin: 0 0 1.6em 0;
  padding: 14px 16px;
  border: 1px solid var(--rule); border-radius: 8px;
}
.test-question .question { margin: 0 0 0.6em 0; }
.test-choices { list-style: none; padding-left: 0; margin: 0.4em 0 0 0; }
.test-choices > li { margin: 0.35em 0; padding: 0; }
.test-choices label {
  display: block; cursor: pointer;
  padding: 8px 12px; border-radius: 6px; border: 1px solid transparent;
  transition: background 0.12s, border-color 0.12s;
}
.test-choices label:hover { background: rgba(214, 0, 108, 0.04); }
.test-choices input[type="radio"] {
  margin-right: 10px;
  accent-color: var(--brand);
  transform: translateY(1px);
}
.test-choices label.choice-correct {
  background: rgba(0, 128, 0, 0.10);
  border-color: #008000;
}
.test-choices label.choice-wrong {
  background: rgba(187, 0, 0, 0.10);
  border-color: #BB0000;
}
.test-choices label.choice-correct::after,
.test-choices label.choice-wrong::after {
  font-weight: 700; margin-left: 8px; font-size: 0.85rem;
}
.test-choices label.choice-correct::after {
  content: "Correct"; color: #008000;
}
.test-choices label.choice-wrong::after {
  content: "Your pick"; color: #BB0000;
}
.test-explanation {
  margin-top: 0.6em; padding: 10px 14px;
  background: rgba(214, 0, 108, 0.04);
  border-left: 3px solid var(--brand);
  border-radius: 0 6px 6px 0;
  font-size: 0.95rem;
}
.test-submit {
  display: block; width: 100%; max-width: 320px; margin: 1.4em auto 0 auto;
  padding: 14px 24px; font-family: inherit; font-size: 1rem; font-weight: 700;
  background: var(--brand); color: white; border: none;
  border-radius: 8px; cursor: pointer;
}
.test-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.test-results-panel {
  margin-top: 1.4em; padding: 24px 24px;
  border: 2px solid var(--brand); border-radius: 10px;
  text-align: center;
}
.test-results-panel .score {
  font-size: 2.4rem; font-weight: 800; color: var(--brand);
  margin: 0 0 0.2em 0;
}
.test-results-panel .pct {
  font-size: 1.1rem; color: var(--muted); margin: 0 0 0.8em 0;
}
.test-passfail {
  display: inline-block; padding: 6px 16px; border-radius: 999px;
  font-weight: 700; font-size: 0.95rem; margin: 0 0 1em 0;
}
.test-passfail.pass { background: rgba(0, 128, 0, 0.12); color: #008000; }
.test-passfail.fail { background: rgba(187, 0, 0, 0.12); color: #BB0000; }
.test-reveal-btn {
  font-family: inherit; font-size: 0.95rem; font-weight: 600;
  padding: 10px 18px; border-radius: 6px; cursor: pointer;
  background: var(--bg); color: var(--brand);
  border: 2px solid var(--brand);
}
.test-empty {
  padding: 24px; border: 1px dashed var(--brand); border-radius: 8px;
  background: rgba(214, 0, 108, 0.03);
  text-align: center; color: var(--muted);
}
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


# --------------------------------------------------------------------------
# Test mode (course final): interactive form with score + reveal.
# --------------------------------------------------------------------------

def detect_quiz_mode(yaml_path: Path, data: Optional[dict] = None) -> str:
    """Return 'test' or 'study' for a quiz YAML file.

    Convention:
    - Anything in exam/ at the course root is test mode.
    - Anything named knowledge-check.yaml in a unit folder is study mode.
    A top-level mode: key (or one nested under quiz: / final_assessment:)
    overrides the convention.
    """
    if data is None:
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}
    explicit = data.get("mode")
    if not explicit and isinstance(data.get("quiz"), dict):
        explicit = data["quiz"].get("mode")
    if not explicit and isinstance(data.get("final_assessment"), dict):
        explicit = data["final_assessment"].get("mode")
    if explicit in ("test", "study"):
        return explicit
    if yaml_path.parent.name == "exam":
        return "test"
    return "study"


def _load_course_final(course_root: Path) -> Optional[dict]:
    """Return the final_assessment dict from exam/course-final.yaml or None."""
    path = course_root / "exam" / "course-final.yaml"
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    final = data.get("final_assessment", {})
    return final if isinstance(final, dict) else None


def _render_test_question(idx: int, q: dict, q_id: str) -> str:
    """Render one test-mode question with radio choices and a hidden explanation."""
    question_text = (q.get("question") or "").strip()
    choices = q.get("choices") or []
    explanation = (q.get("explanation") or "").strip()

    correct_indices = [i for i, c in enumerate(choices) if c.get("correct")]
    correct_attr = ",".join(str(i) for i in correct_indices)

    question_html = "<br>\n".join(_esc(line) for line in question_text.splitlines())

    choice_lis = []
    for i, c in enumerate(choices):
        choice_text = _esc(c.get("text", ""))
        radio_id = f"{q_id}-c{i}"
        choice_lis.append(
            f'    <li>'
            f'<label for="{radio_id}">'
            f'<input type="radio" id="{radio_id}" name="{q_id}" value="{i}">'
            f'<span class="choice-text">{choice_text}</span>'
            f'</label></li>'
        )
    choices_html = "\n".join(choice_lis)

    explanation_paras = []
    for para in explanation.split("\n\n"):
        para = para.strip()
        if para:
            explanation_paras.append(f"<p>{_esc(para)}</p>")
    explanation_html = "\n".join(explanation_paras)

    return (
        f'<div class="test-question" data-q-id="{_esc(q_id)}" data-correct-indices="{correct_attr}">\n'
        f'  <p class="question">{question_html}</p>\n'
        f'  <ul class="test-choices">\n{choices_html}\n  </ul>\n'
        f'  <div class="test-explanation" hidden>\n'
        f'    <p><strong>Why:</strong></p>\n'
        f'    {explanation_html}\n'
        f'  </div>\n'
        f'</div>'
    )


_TEST_MODE_JS = """\
<script>
(function () {
  document.querySelectorAll('.test-section').forEach(function (section) {
    initTestSection(section);
  });

  function shuffle(arr) {
    for (var i = arr.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = arr[i]; arr[i] = arr[j]; arr[j] = t;
    }
    return arr;
  }

  function initTestSection(section) {
    var perAttempt = parseInt(section.dataset.perAttempt, 10) || 0;
    var passThreshold = parseFloat(section.dataset.passThreshold) || 0;
    var allQuestions = Array.prototype.slice.call(
      section.querySelectorAll('.test-question')
    );
    if (allQuestions.length === 0) return;

    // Random sample: hide questions beyond perAttempt
    var perAttemptShown = perAttempt > 0
      ? Math.min(perAttempt, allQuestions.length)
      : allQuestions.length;
    var indices = allQuestions.map(function (_, i) { return i; });
    shuffle(indices);
    var pickedSet = {};
    for (var i = 0; i < perAttemptShown; i++) pickedSet[indices[i]] = true;
    allQuestions.forEach(function (q, i) {
      if (!pickedSet[i]) {
        q.style.display = 'none';
        q.classList.add('not-picked');
      }
    });

    var visible = allQuestions.filter(function (q) {
      return !q.classList.contains('not-picked');
    });

    var progressEl = section.querySelector('.test-progress-text');
    var totalText = section.querySelector('.test-progress-total');
    if (totalText) totalText.textContent = perAttemptShown;
    updateProgress();

    section.addEventListener('change', function (e) {
      if (e.target && e.target.type === 'radio') updateProgress();
    });

    function updateProgress() {
      var answered = 0;
      visible.forEach(function (q) {
        if (q.querySelector('input[type=radio]:checked')) answered++;
      });
      if (progressEl) progressEl.textContent = answered;
    }

    var form = section.querySelector('.test-form');
    var submitBtn = section.querySelector('.test-submit');
    var resultsPanel = section.querySelector('.test-results-panel');
    var revealBtn = section.querySelector('.test-reveal-btn');
    var scoreEl = section.querySelector('.test-results-panel .score');
    var pctEl = section.querySelector('.test-results-panel .pct');
    var passfailEl = section.querySelector('.test-passfail');

    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var correct = 0;
        var thresholdPct = Math.round(passThreshold * 100);
        visible.forEach(function (q) {
          var raw = (q.dataset.correctIndices || '').split(',').filter(Boolean);
          var correctSet = {};
          raw.forEach(function (s) { correctSet[parseInt(s, 10)] = true; });
          var picked = q.querySelector('input[type=radio]:checked');
          if (picked && correctSet[parseInt(picked.value, 10)]) {
            correct++;
            q.dataset.outcome = 'right';
          } else {
            q.dataset.outcome = picked ? 'wrong' : 'unanswered';
          }
        });
        var total = visible.length;
        var pct = total > 0 ? correct / total : 0;
        if (scoreEl) scoreEl.textContent = correct + ' of ' + total;
        if (pctEl) pctEl.textContent = Math.round(pct * 100) + ' percent';
        if (passfailEl) {
          if (pct >= passThreshold) {
            passfailEl.textContent = 'Passed (threshold ' + thresholdPct + ' percent)';
            passfailEl.className = 'test-passfail pass';
          } else {
            passfailEl.textContent = 'Did not pass (threshold ' + thresholdPct + ' percent)';
            passfailEl.className = 'test-passfail fail';
          }
        }

        // Hide form, show results
        form.querySelectorAll('.test-question').forEach(function (q) {
          q.style.display = 'none';
        });
        if (submitBtn) submitBtn.style.display = 'none';
        var progressBar = section.querySelector('.test-progress');
        if (progressBar) progressBar.style.display = 'none';
        if (resultsPanel) resultsPanel.hidden = false;
      });
    }

    if (revealBtn) {
      revealBtn.addEventListener('click', function () {
        // Re-show the picked questions, locked, color-coded, with explanations
        visible.forEach(function (q) {
          q.style.display = '';
          var raw = (q.dataset.correctIndices || '').split(',').filter(Boolean);
          var correctSet = {};
          raw.forEach(function (s) { correctSet[parseInt(s, 10)] = true; });
          var picked = q.querySelector('input[type=radio]:checked');
          var pickedIdx = picked ? parseInt(picked.value, 10) : -1;
          var labels = q.querySelectorAll('.test-choices label');
          labels.forEach(function (label, i) {
            var input = label.querySelector('input[type=radio]');
            if (input) input.disabled = true;
            if (correctSet[i]) {
              label.classList.add('choice-correct');
            } else if (i === pickedIdx) {
              label.classList.add('choice-wrong');
            }
          });
          var explanationEl = q.querySelector('.test-explanation');
          if (explanationEl) explanationEl.hidden = false;
        });
        revealBtn.style.display = 'none';
      });
    }
  }
})();
</script>
"""


def render_test_section(quiz_data: dict, section_id: str = "course-final-test",
                         heading: str = "Final Assessment",
                         intro: Optional[str] = None) -> str:
    """Return the HTML for a test-mode quiz section.

    quiz_data is the inner dict from the YAML (the value under final_assessment:
    or quiz:). The renderer:
    - Embeds every question in the page; an inline JS shuffle hides any
      beyond questions_per_attempt on each load.
    - Handles small or empty banks gracefully via min(bank, per_attempt).
    """
    questions = quiz_data.get("questions") or []
    bank_size = len(questions)
    per_attempt_raw = quiz_data.get("questions_per_attempt")
    pass_threshold = quiz_data.get("pass_threshold", 0.75)
    try:
        pass_threshold = float(pass_threshold)
    except (TypeError, ValueError):
        pass_threshold = 0.75

    if bank_size == 0:
        return (
            f'<section class="test-section" id="{_esc(section_id)}">\n'
            f'  <h2>{_esc(heading)}</h2>\n'
            f'  <div class="test-empty">\n'
            f'    <p><strong>Test mode preview, no questions yet.</strong></p>\n'
            f'    <p>Run <code>bes build-final</code> to generate the question bank.</p>\n'
            f'  </div>\n'
            f'</section>'
        )

    if per_attempt_raw is None:
        per_attempt = bank_size
    else:
        try:
            per_attempt = int(per_attempt_raw)
        except (TypeError, ValueError):
            per_attempt = bank_size
    per_attempt = max(0, min(per_attempt, bank_size))
    if per_attempt == 0:
        per_attempt = bank_size

    # Meta line
    meta_lines = []
    if bank_size < (per_attempt_raw or bank_size):
        meta_lines.append(
            f"Test mode preview with {per_attempt} of "
            f"{per_attempt_raw} target questions available "
            f"(bank has {bank_size})."
        )
    else:
        meta_lines.append(
            f"Test mode. Each load samples {per_attempt} of "
            f"{bank_size} bank questions. Refresh for a new set."
        )
    meta_lines.append(
        f"Pass threshold: {round(pass_threshold * 100)} percent."
    )
    meta_html = "<br>\n".join(_esc(line) for line in meta_lines)

    intro_html = ""
    if intro:
        intro_html = f'  <p class="test-intro">{_esc(intro)}</p>\n'

    # Render every question; JS hides those beyond perAttempt
    question_blocks = []
    for i, q in enumerate(questions):
        q_id = q.get("id") or f"final-q{i+1:03d}"
        question_blocks.append(_render_test_question(i, q, _safe_q_id(q_id)))
    questions_html = "\n".join(question_blocks)

    return (
        f'<section class="test-section" id="{_esc(section_id)}" '
        f'data-per-attempt="{per_attempt}" '
        f'data-pass-threshold="{pass_threshold}">\n'
        f'  <h2>{_esc(heading)}</h2>\n'
        f'  <p class="test-meta">{meta_html}</p>\n'
        f'{intro_html}'
        f'  <form class="test-form">\n'
        f'    <div class="test-progress">\n'
        f'      <span><span class="test-progress-text">0</span> of '
        f'<span class="test-progress-total">{per_attempt}</span> answered</span>\n'
        f'    </div>\n'
        f'    <div class="test-questions">\n{questions_html}\n    </div>\n'
        f'    <button type="submit" class="test-submit">Submit</button>\n'
        f'  </form>\n'
        f'  <div class="test-results-panel" hidden>\n'
        f'    <div class="score"></div>\n'
        f'    <div class="pct"></div>\n'
        f'    <div><span class="test-passfail"></span></div>\n'
        f'    <button type="button" class="test-reveal-btn">Show correct answers and explanations</button>\n'
        f'  </div>\n'
        f'</section>'
    )


_Q_ID_SAFE_RE = re.compile(r"[^A-Za-z0-9_-]+")


def _safe_q_id(raw: str) -> str:
    """Return a string safe to use as an HTML name/id attribute."""
    s = _Q_ID_SAFE_RE.sub("-", str(raw)).strip("-")
    return s or "q"


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


# --------------------------------------------------------------------------
# Course-level preview: every unit on one page with a TOC.
# --------------------------------------------------------------------------

_COURSE_CSS_OVERRIDES = """\
html { scroll-behavior: smooth; }
.container { max-width: 800px; }
.course-tagline {
  font-size: 1.05rem; color: var(--muted); font-style: italic;
  margin: 0.4em 0 1.6em 0;
}
.toc {
  background: rgba(214, 0, 108, 0.04);
  border-left: 3px solid var(--brand);
  border-radius: 0 6px 6px 0;
  padding: 12px 18px 12px 36px;
  margin: 0 0 2.4em 0;
  font-size: 0.98rem;
}
.toc li { margin: 0.35em 0; }
.toc a { font-weight: 600; }
.unit { padding-top: 1em; }
.unit + .unit { margin-top: 1em; border-top: 1px solid var(--rule); }
.outcomes {
  font-size: 0.95rem; color: var(--muted);
  background: rgba(214, 0, 108, 0.03);
  border-radius: 6px; padding: 10px 16px 10px 32px;
  margin: 0.4em 0 1.4em 0;
}
.outcomes li { margin: 0.25em 0; }
.empty {
  color: var(--muted); font-size: 0.95rem; margin: 1em 0;
}
.back-to-top {
  display: block; text-align: center;
  margin: 2.4em 0 0.6em 0; padding: 14px 0;
  border-top: 1px solid var(--rule);
  font-size: 0.9rem;
}
"""


def _gather_units(course_root: Path) -> list[tuple[Path, Unit, dict]]:
    """Return a list of (unit_folder, Unit, raw unit dict) sorted by folder name."""
    out = []
    content_root = course_root / "content"
    if not content_root.exists():
        return out
    for unit_folder in sorted(content_root.glob("unit-*")):
        if not unit_folder.is_dir():
            continue
        unit_yaml_path = unit_folder / "unit.yaml"
        if not unit_yaml_path.exists():
            continue
        unit_data = (yaml.safe_load(unit_yaml_path.read_text(encoding="utf-8")) or {}).get("unit", {})
        out.append((unit_folder, _load_unit(unit_folder), unit_data))
    return out


def render_course_preview(course_root: Path) -> str:
    """Render the entire course (every unit, plus the course final) into one
    self-contained HTML page string."""
    course_meta = _load_course_meta(course_root)
    md = _make_md()
    units_info = _gather_units(course_root)
    final_data = _load_course_final(course_root)
    final_name = (final_data or {}).get("name") or "Final Assessment"
    has_final = final_data is not None

    course_h1 = _esc(course_meta.course_name)
    page_title = f"{course_meta.course_name} Course Preview"
    tagline_html = (
        f'    <p class="course-tagline">{_esc(course_meta.tagline)}</p>\n'
        if course_meta.tagline else ""
    )

    # Table of contents
    toc_items = [
        f'<li><a href="#unit-{u.number}">Unit {u.number}: {_esc(u.title)}</a></li>'
        for _folder, u, _raw in units_info
    ]
    if has_final:
        toc_items.append(
            f'<li><a href="#course-final-test">{_esc(final_name)}</a></li>'
        )
    toc_html = (
        "<nav>\n"
        "  <h2>Contents</h2>\n"
        f'  <ol class="toc">\n    ' + "\n    ".join(toc_items) + "\n  </ol>\n"
        "</nav>"
    ) if toc_items else ""

    # Per-unit sections
    unit_sections: list[str] = []
    for unit_folder, unit, raw in units_info:
        outcomes = raw.get("learning_outcomes") or []
        outcomes_html = ""
        if outcomes:
            items = "\n    ".join(f"<li>{_esc(o)}</li>" for o in outcomes)
            outcomes_html = (
                f'  <ul class="outcomes">\n    {items}\n  </ul>'
            )

        if unit.lessons:
            blocks = []
            for lesson in unit.lessons:
                expanded = _expand_microsim_directives(lesson.body_markdown, unit.number)
                body_html = _render_with_mermaid(md, expanded)
                blocks.append(
                    '  <section class="lesson">\n'
                    f"    <h3>{_esc(lesson.title)}</h3>\n"
                    f"{body_html}"
                    "  </section>"
                )
            lessons_html = "\n".join(blocks)
        else:
            lessons_html = '  <p class="empty"><em>Lessons coming soon.</em></p>'

        if unit.knowledge_check:
            kc_items = "\n".join(
                _render_question(i, q) for i, q in enumerate(unit.knowledge_check)
            )
            kc_html = (
                '  <section class="kc">\n'
                '    <h3>Knowledge Check</h3>\n'
                f'    <ol class="kc-list">\n{kc_items}\n    </ol>\n'
                '  </section>'
            )
        else:
            kc_html = ""

        unit_sections.append(
            f'<section class="unit" id="unit-{unit.number}">\n'
            f'  <h2>Unit {unit.number}: {_esc(unit.title)}</h2>\n'
            f'{outcomes_html}\n'
            f'{lessons_html}\n'
            f'{kc_html}\n'
            '</section>'
        )

    units_html = "\n\n".join(unit_sections) if unit_sections else (
        '<p class="empty"><em>No units found in this course.</em></p>'
    )

    final_html = ""
    test_js = ""
    if has_final:
        final_html = render_test_section(
            final_data,
            section_id="course-final-test",
            heading=final_name,
        )
        test_js = _TEST_MODE_JS

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(page_title)}</title>
  <style>
{_CSS}{_COURSE_CSS_OVERRIDES}</style>
  {_MERMAID_HEAD}
</head>
<body id="top">
  <div class="container">
    <h1>{course_h1}</h1>
{tagline_html}
{toc_html}

{units_html}

{final_html}

    <a class="back-to-top" href="#top">Back to top &uarr;</a>
  </div>
  {_MERMAID_INIT}
  {test_js}
</body>
</html>
"""


def write_course_preview(course_root: Path, output_dir: Path) -> Path:
    """Render the course-level preview, write it to output_dir/course-preview.html,
    and copy every unit's microsims folder to output_dir/unit-NN-microsims/.
    Returns the path to the written HTML file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    html = render_course_preview(course_root)
    out_path = output_dir / "course-preview.html"
    out_path.write_text(html, encoding="utf-8")

    content_root = course_root / "content"
    if content_root.exists():
        for unit_folder in sorted(content_root.glob("unit-*")):
            if not unit_folder.is_dir():
                continue
            unit_yaml_path = unit_folder / "unit.yaml"
            if not unit_yaml_path.exists():
                continue
            meta = (yaml.safe_load(unit_yaml_path.read_text(encoding="utf-8")) or {}).get("unit", {})
            n = int(meta.get("number", 0) or 0)
            microsims_src = unit_folder / "microsims"
            if microsims_src.exists() and microsims_src.is_dir():
                microsims_dst = output_dir / f"unit-{n:02d}-microsims"
                if microsims_dst.exists():
                    shutil.rmtree(microsims_dst)
                shutil.copytree(microsims_src, microsims_dst)

    return out_path


# --------------------------------------------------------------------------
# Standalone final preview: just the course final, in test mode.
# --------------------------------------------------------------------------

def render_final_preview(course_root: Path) -> str:
    """Render a self-contained HTML page that shows only the course final."""
    course_meta = _load_course_meta(course_root)
    final_data = _load_course_final(course_root)
    course_h1 = _esc(course_meta.course_name)
    final_name = (final_data or {}).get("name") or "Final Assessment"
    page_title = f"{course_meta.course_name} Final Preview"

    if final_data is None:
        body_html = (
            '<section class="test-section">\n'
            '  <h2>No final assessment found.</h2>\n'
            '  <div class="test-empty">\n'
            '    <p>No <code>exam/course-final.yaml</code> at the course root.</p>\n'
            '    <p>Run <code>bes build-final</code> to generate one.</p>\n'
            '  </div>\n'
            '</section>'
        )
        test_js = ""
    else:
        body_html = render_test_section(
            final_data,
            section_id="course-final-test",
            heading=final_name,
        )
        test_js = _TEST_MODE_JS

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(page_title)}</title>
  <style>
{_CSS}{_COURSE_CSS_OVERRIDES}</style>
</head>
<body id="top">
  <div class="container">
    <h1>{course_h1}</h1>
{body_html}
    <a class="back-to-top" href="#top">Back to top &uarr;</a>
  </div>
  {test_js}
</body>
</html>
"""


def write_final_preview(course_root: Path, output_dir: Path) -> Path:
    """Render the standalone final preview to output_dir/final-preview.html."""
    output_dir.mkdir(parents=True, exist_ok=True)
    html = render_final_preview(course_root)
    out_path = output_dir / "final-preview.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path
