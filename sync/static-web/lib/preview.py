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
from dataclasses import dataclass, field
from html import escape as _esc
from pathlib import Path
from typing import Optional

import yaml
from markdown_it import MarkdownIt
from markdown_it.token import Token

from .layout import (
    PROGRESS_AND_ANIMATION_JS,
    reading_time_minutes,
    render_footer,
    render_hero,
    render_lesson_card,
    render_sidebar,
    render_unit_card,
    render_unit_card_grid,
)


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
    course_slug: str = ""
    # Phase: layered knowledge_check_mode. Course-config sets the default
    # for every unit's knowledge-check.yaml in this course. A unit's quiz
    # YAML may override via its own `mode:` key. Falls back to "study".
    knowledge_check_mode: str = "study"
    # Phase 18 visual polish: optional course-config fields. All graceful
    # defaults so existing courses render cleanly without explicit values.
    cover_image_url: str = ""
    logo_url: str = ""
    brand_secondary_color: str = ""
    license_text: str = ""
    author_credit: str = "Backstage Essentials LLC"


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
    # Phase: per-quiz mode override read from the unit's knowledge-check.yaml.
    # Either "study", "test", or None (falls back to course/toolkit default).
    knowledge_check_mode_override: Optional[str] = None
    # Whole quiz dict from the YAML (under quiz:). Used by test-mode
    # rendering to access pass_threshold and similar fields.
    knowledge_check_data: dict = field(default_factory=dict)


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
    kc_data: dict = {}
    kc_mode_override: Optional[str] = None
    if kc_path.exists():
        kc_yaml = yaml.safe_load(kc_path.read_text(encoding="utf-8")) or {}
        # Per-quiz mode override may live at the top of the YAML or
        # nested under quiz: — accept either.
        explicit_mode = kc_yaml.get("mode")
        kc = kc_yaml.get("quiz", {})
        if not explicit_mode and isinstance(kc, dict):
            explicit_mode = kc.get("mode")
        if explicit_mode in ("study", "test"):
            kc_mode_override = explicit_mode
        kc_questions = kc.get("questions") or []
        if kc.get("title"):
            kc_title = kc["title"]
        kc_data = kc

    return Unit(
        number=int(unit_data.get("number", 0) or 0),
        title=str(unit_data.get("title", unit_folder.name)),
        lessons=lessons,
        knowledge_check=kc_questions,
        knowledge_check_title=kc_title,
        knowledge_check_mode_override=kc_mode_override,
        knowledge_check_data=kc_data,
    )


_TAGLINE_MAX_CHARS = 200


def _tagline_from_description(course_root: Path) -> str:
    """Extract a hero-friendly tagline from course-description.md.

    Pulls the first non-heading paragraph, then narrows to its first
    sentence so a long Pitch paragraph does not blow up the hero.
    Falls back to a 200-char truncation with ellipsis if no sentence
    boundary is found in range.
    """
    desc_path = course_root / "course-description.md"
    if not desc_path.exists():
        return ""
    paragraph = ""
    for chunk in desc_path.read_text(encoding="utf-8").split("\n\n"):
        stripped = chunk.strip()
        if not stripped or stripped.startswith("#"):
            continue
        paragraph = stripped.replace("\n", " ")
        break
    if not paragraph:
        return ""
    # Prefer the first sentence. Match ". ", "! ", "? " followed by a
    # capital-leading word, or end-of-string punctuation.
    match = re.search(r"([\.!?])(\s+)(?=[A-Z0-9])", paragraph)
    if match:
        first_sentence = paragraph[: match.end(1)].strip()
        if len(first_sentence) <= _TAGLINE_MAX_CHARS:
            return first_sentence
    if len(paragraph) <= _TAGLINE_MAX_CHARS:
        return paragraph
    return paragraph[: _TAGLINE_MAX_CHARS - 1].rstrip() + "…"


def _load_course_meta(course_root: Path) -> CourseMeta:
    config = (yaml.safe_load((course_root / "course-config.yaml").read_text(encoding="utf-8")) or {})
    course = config.get("course", {})
    name = course.get("name", "Course")
    slug = course.get("slug", "")
    kc_mode_raw = course.get("knowledge_check_mode")
    kc_mode = kc_mode_raw if kc_mode_raw in ("study", "test") else "study"
    cover_image_url = course.get("cover_image_url") or ""
    logo_url = course.get("logo_url") or ""
    brand_secondary_color = course.get("brand_secondary_color") or ""
    license_text = course.get("license_text") or ""
    author_credit = course.get("author_credit") or "Backstage Essentials LLC"

    tagline = (course.get("tagline") or "").strip()
    if not tagline:
        tagline = _tagline_from_description(course_root)
    return CourseMeta(course_name=name, tagline=tagline, course_slug=slug,
                      knowledge_check_mode=kc_mode,
                      cover_image_url=cover_image_url,
                      logo_url=logo_url,
                      brand_secondary_color=brand_secondary_color,
                      license_text=license_text,
                      author_credit=author_credit)


# --------------------------------------------------------------------------
# Page assembly.
# --------------------------------------------------------------------------

_STYLE_CSS_PATH = Path(__file__).resolve().parent / "style.css"
_CSS_CACHE: Optional[str] = None


def _load_css() -> str:
    """Read style.css from this skill's lib/ folder.

    Cached after first read so render-heavy code paths do not re-hit disk.
    """
    global _CSS_CACHE
    if _CSS_CACHE is None:
        try:
            _CSS_CACHE = _STYLE_CSS_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            _CSS_CACHE = "/* style.css not found */"
    return _CSS_CACHE

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

def detect_quiz_mode(yaml_path: Path, data: Optional[dict] = None,
                       course_kc_default: str = "study") -> str:
    """Return 'test' or 'study' for a quiz YAML file.

    Resolution order:
    1. Explicit `mode:` key in the YAML (top-level or nested under quiz: /
       final_assessment:). Always wins.
    2. Convention: anything in exam/ at the course root is "test".
    3. course_kc_default — the course-config.yaml `knowledge_check_mode`
       value, applied to non-exam quizzes (i.e., unit knowledge checks).
       Defaults to "study" so older callers keep their existing behavior.
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
    if course_kc_default in ("study", "test"):
        return course_kc_default
    return "study"


def resolve_kc_mode(unit: "Unit", course_meta: "CourseMeta") -> str:
    """Resolve the knowledge-check render mode for one unit.

    Layered: per-quiz override (in knowledge-check.yaml) wins; otherwise
    the course-config knowledge_check_mode wins; otherwise "study".
    """
    if unit.knowledge_check_mode_override in ("study", "test"):
        return unit.knowledge_check_mode_override
    if course_meta.knowledge_check_mode in ("study", "test"):
        return course_meta.knowledge_check_mode
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
  // Phase 14: localStorage-backed retest tracking with overlap-aware sampling.

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

  function readAttempts(section) {
    var key = section.dataset.storageKey || '';
    var persist = section.dataset.persistAttempts !== 'false';
    if (!key || !persist) return [];
    try {
      var raw = window.localStorage.getItem(key);
      if (!raw) return [];
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  }

  function writeAttempts(section, attempts) {
    var key = section.dataset.storageKey || '';
    var persist = section.dataset.persistAttempts !== 'false';
    if (!key || !persist) return;
    try {
      window.localStorage.setItem(key, JSON.stringify(attempts));
    } catch (e) {}
  }

  function clearAttempts(section) {
    var key = section.dataset.storageKey || '';
    if (!key) return;
    try { window.localStorage.removeItem(key); } catch (e) {}
  }

  // Pick the question set for the current attempt given prior attempts.
  // Strategy: prefer fully-fresh sample; if fresh pool is too small, fill
  // with overlap up to floor(maxOverlap * perAttempt), preferring questions
  // the student answered wrong on prior attempts.
  function sampleForAttempt(allQIds, perAttempt, priorAttempts, maxOverlap) {
    var seen = {};
    var wrongSet = {};
    priorAttempts.forEach(function (a) {
      (a.question_ids || []).forEach(function (qid) { seen[qid] = true; });
      (a.wrong_ids || []).forEach(function (qid) { wrongSet[qid] = true; });
    });
    var fresh = allQIds.filter(function (qid) { return !seen[qid]; });
    var overlap = allQIds.filter(function (qid) { return seen[qid]; });
    shuffle(fresh);
    shuffle(overlap);

    if (fresh.length >= perAttempt) {
      return fresh.slice(0, perAttempt);
    }
    var overlapCap = Math.floor(maxOverlap * perAttempt);
    var needed = perAttempt - fresh.length;
    var overlapCount = Math.min(needed, overlapCap, overlap.length);
    // Prefer previously-wrong questions when we must reuse.
    overlap.sort(function (a, b) {
      var aw = wrongSet[a] ? 0 : 1;
      var bw = wrongSet[b] ? 0 : 1;
      return aw - bw;
    });
    var chosen = fresh.concat(overlap.slice(0, overlapCount));
    // If we still cannot fill perAttempt, return what we have rather than
    // breaking the constraint. The validator should have caught this case.
    return chosen;
  }

  function initTestSection(section) {
    var perAttempt = parseInt(section.dataset.perAttempt, 10) || 0;
    var passThreshold = parseFloat(section.dataset.passThreshold) || 0;
    var maxAttempts = parseInt(section.dataset.maxAttempts, 10) || 1;
    var maxOverlap = parseFloat(section.dataset.maxOverlap);
    if (isNaN(maxOverlap)) maxOverlap = 0.10;
    var lockoutMessage = section.dataset.lockoutMessage || '';
    // Phase: simple-mode test sections skip attempt tracking entirely.
    // Used for unit knowledge checks rendered in test mode (formative).
    var simpleMode = section.dataset.simpleMode === 'true';

    var allQuestions = Array.prototype.slice.call(
      section.querySelectorAll('.test-question')
    );
    if (allQuestions.length === 0) return;

    var qById = {};
    var allQIds = allQuestions.map(function (q) {
      var qid = q.dataset.qId;
      qById[qid] = q;
      return qid;
    });

    // Honor ?reset=true for course authors testing the page.
    if (/\\b[?&]reset=true\\b/.test(window.location.search)) {
      clearAttempts(section);
    }

    var attempts = readAttempts(section);

    // Always show the reset button when localStorage is in use; it stays
    // hidden by default but a query param flips it on so authors can wipe
    // saved state without dev tools.
    var resetBtn = section.querySelector('.test-reset-btn');
    if (resetBtn && /\\b[?&]author=true\\b/.test(window.location.search)) {
      resetBtn.hidden = false;
      resetBtn.addEventListener('click', function () {
        clearAttempts(section);
        window.location.reload();
      });
    }

    // Lockout: at or above max_attempts. Skipped in simple mode.
    if (!simpleMode && attempts.length >= maxAttempts && maxAttempts >= 1) {
      renderLockout(section, lockoutMessage, attempts);
      return;
    }

    var attemptNumber = attempts.length + 1;
    if (!simpleMode) {
      showAttemptCounter(section, attemptNumber, maxAttempts);
    }

    // Sample questions for this attempt.
    var picked = sampleForAttempt(
      allQIds,
      Math.min(perAttempt, allQIds.length),
      attempts,
      maxOverlap
    );
    var pickedSet = {};
    picked.forEach(function (qid) { pickedSet[qid] = true; });
    allQuestions.forEach(function (q) {
      if (!pickedSet[q.dataset.qId]) {
        q.style.display = 'none';
        q.classList.add('not-picked');
      }
    });

    var visible = allQuestions.filter(function (q) {
      return !q.classList.contains('not-picked');
    });

    var progressEl = section.querySelector('.test-progress-text');
    var totalText = section.querySelector('.test-progress-total');
    if (totalText) totalText.textContent = visible.length;
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
    var retryPrompt = section.querySelector('.test-retry-prompt');
    var retryBtn = section.querySelector('.test-retry-btn');

    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var correct = 0;
        var thresholdPct = Math.round(passThreshold * 100);
        var wrongIds = [];
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
            wrongIds.push(q.dataset.qId);
          }
        });
        var total = visible.length;
        var pct = total > 0 ? correct / total : 0;
        var passed = pct >= passThreshold;
        if (scoreEl) scoreEl.textContent = correct + ' of ' + total;
        if (pctEl) pctEl.textContent = Math.round(pct * 100) + ' percent';
        if (passfailEl) {
          if (passed) {
            passfailEl.textContent = 'Passed (threshold ' + thresholdPct + ' percent)';
            passfailEl.className = 'test-passfail pass';
          } else {
            passfailEl.textContent = 'Did not pass (threshold ' + thresholdPct + ' percent)';
            passfailEl.className = 'test-passfail fail';
          }
        }

        // Persist this attempt.
        var record = {
          attempt_number: attemptNumber,
          question_ids: visible.map(function (q) { return q.dataset.qId; }),
          wrong_ids: wrongIds,
          score: pct,
          passed: passed,
          timestamp: new Date().toISOString()
        };
        attempts.push(record);
        writeAttempts(section, attempts);

        // Hide form, show results
        form.querySelectorAll('.test-question').forEach(function (q) {
          q.style.display = 'none';
        });
        if (submitBtn) submitBtn.style.display = 'none';
        var progressBar = section.querySelector('.test-progress');
        if (progressBar) progressBar.style.display = 'none';
        if (resultsPanel) resultsPanel.hidden = false;

        // Retest prompt. Simple-mode KCs always allow a retake; the
        // course final flows through the Phase 14 retest/lockout logic.
        if (simpleMode) {
          if (retryPrompt) {
            retryPrompt.textContent = passed
              ? 'Passed. Refresh or click below to take it again.'
              : 'Did not pass. Refresh or click below to take it again.';
            retryPrompt.hidden = false;
          }
          if (retryBtn) {
            retryBtn.textContent = 'Retake';
            retryBtn.hidden = false;
            retryBtn.addEventListener('click', function () {
              window.location.reload();
            });
          }
        } else {
          var attemptsLeft = maxAttempts - attempts.length;
          if (passed) {
            if (retryPrompt) {
              retryPrompt.textContent = 'You passed. Retests are not required.';
              retryPrompt.hidden = false;
            }
          } else if (attemptsLeft > 0) {
            if (retryPrompt) {
              retryPrompt.textContent =
                'You can retake this exam. ' + attemptsLeft + ' attempt' +
                (attemptsLeft === 1 ? '' : 's') + ' remaining.';
              retryPrompt.hidden = false;
            }
            if (retryBtn) {
              retryBtn.hidden = false;
              retryBtn.addEventListener('click', function () {
                window.location.reload();
              });
            }
          } else {
            if (retryPrompt) {
              retryPrompt.textContent = lockoutMessage;
              retryPrompt.hidden = false;
            }
          }
        }
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

  function renderLockout(section, message, attempts) {
    var form = section.querySelector('.test-form');
    if (form) form.style.display = 'none';
    var lockoutEl = section.querySelector('.test-lockout');
    var msgEl = section.querySelector('.test-lockout-message');
    if (msgEl) msgEl.textContent = message;
    if (lockoutEl) lockoutEl.hidden = false;
    var counter = section.querySelector('.test-attempt-counter');
    if (counter) {
      counter.textContent = 'Used ' + attempts.length + ' of ' +
        (parseInt(section.dataset.maxAttempts, 10) || attempts.length) + ' attempts.';
      counter.hidden = false;
    }
  }

  function showAttemptCounter(section, attemptNumber, maxAttempts) {
    var counter = section.querySelector('.test-attempt-counter');
    if (!counter) return;
    if (maxAttempts > 1) {
      counter.textContent = 'Attempt ' + attemptNumber + ' of ' + maxAttempts + '.';
      counter.hidden = false;
    }
  }
})();
</script>
"""


_DEFAULT_LOCKOUT_MESSAGE = (
    "You have used all available attempts. Please contact your "
    "instructor if you need additional review."
)


def render_test_section(quiz_data: dict, section_id: str = "course-final-test",
                         heading: str = "Final Assessment",
                         intro: Optional[str] = None,
                         course_slug: str = "",
                         simple_mode: bool = False,
                         unit_number: Optional[int] = None) -> str:
    """Return the HTML for a test-mode quiz section.

    quiz_data is the inner dict from the YAML (the value under final_assessment:
    or quiz:). The renderer:
    - Embeds every question in the page. The inline JS samples
      `questions_per_attempt` on each load, with attempt-aware overlap rules
      enforced when Phase 14 retest fields are present.
    - Tracks attempts in localStorage under `course-{slug}-final-attempts`
      when course_slug is provided and attempts_persist_across_sessions is true.
    - Handles small or empty banks gracefully via min(bank, per_attempt).

    simple_mode strips the Phase 14 retest UI: no attempt counter, no
    lockout panel, no localStorage persistence. Used for unit knowledge
    checks rendered in test mode (formative; refresh to retry).
    """
    questions = quiz_data.get("questions") or []
    bank_size = len(questions)
    per_attempt_raw = quiz_data.get("questions_per_attempt")
    pass_threshold = quiz_data.get("pass_threshold", 0.75)
    try:
        pass_threshold = float(pass_threshold)
    except (TypeError, ValueError):
        pass_threshold = 0.75

    # Phase 14 retest fields with sensible defaults.
    try:
        max_attempts = int(quiz_data.get("max_attempts", 3))
    except (TypeError, ValueError):
        max_attempts = 3
    if max_attempts < 1:
        max_attempts = 1

    try:
        max_overlap = float(quiz_data.get("max_overlap_percentage", 0.10))
    except (TypeError, ValueError):
        max_overlap = 0.10
    if max_overlap < 0:
        max_overlap = 0.0
    elif max_overlap > 1:
        max_overlap = 1.0

    persist_raw = quiz_data.get("attempts_persist_across_sessions", True)
    persist = bool(persist_raw) if persist_raw is not None else True

    lockout_msg_raw = quiz_data.get("retest_lockout_message")
    if lockout_msg_raw:
        # Collapse newlines/whitespace so the message fits in an HTML attribute.
        lockout_message = " ".join(str(lockout_msg_raw).split()).strip()
    else:
        lockout_message = _DEFAULT_LOCKOUT_MESSAGE

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
    if simple_mode:
        meta_lines.append(
            f"Test mode. {bank_size} question"
            f"{'s' if bank_size != 1 else ''}."
        )
    elif bank_size < (per_attempt_raw or bank_size):
        meta_lines.append(
            f"Test mode preview with {per_attempt} of "
            f"{per_attempt_raw} target questions available "
            f"(bank has {bank_size})."
        )
    else:
        meta_lines.append(
            f"Test mode. Each attempt samples {per_attempt} of "
            f"{bank_size} bank questions."
        )
    meta_lines.append(
        f"Pass threshold: {round(pass_threshold * 100)} percent."
    )
    if not simple_mode and max_attempts > 1:
        meta_lines.append(
            f"Up to {max_attempts} attempts; retests overlap at most "
            f"{round(max_overlap * 100)} percent with prior attempts."
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

    storage_key = f"course-{course_slug}-final-attempts" if course_slug else ""
    if simple_mode:
        if course_slug and unit_number is not None:
            # Unit KC: persist attempts so course-gating can read pass state.
            storage_key = f"course-{course_slug}-unit-{unit_number}-kc-attempts"
            persist = True
        else:
            persist = False
            storage_key = ""

    return (
        f'<section class="test-section" id="{_esc(section_id)}" '
        f'data-per-attempt="{per_attempt}" '
        f'data-pass-threshold="{pass_threshold}" '
        f'data-max-attempts="{max_attempts}" '
        f'data-max-overlap="{max_overlap}" '
        f'data-persist-attempts="{"true" if persist else "false"}" '
        f'data-simple-mode="{"true" if simple_mode else "false"}" '
        f'data-storage-key="{_esc(storage_key)}" '
        f'data-lockout-message="{_esc(lockout_message)}">\n'
        f'  <h2>{_esc(heading)}</h2>\n'
        f'  <p class="test-meta">{meta_html}</p>\n'
        f'  <p class="test-attempt-counter" hidden></p>\n'
        f'  <div class="test-lockout" hidden>\n'
        f'    <p class="test-lockout-message"></p>\n'
        f'  </div>\n'
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
        f'    <p class="test-retry-prompt" hidden></p>\n'
        f'    <button type="button" class="test-retry-btn" hidden>Start next attempt</button>\n'
        f'    <button type="button" class="test-reveal-btn">Show correct answers and explanations</button>\n'
        f'  </div>\n'
        f'  <button type="button" class="test-reset-btn" hidden>Reset attempts (author only)</button>\n'
        f'</section>'
    )


_Q_ID_SAFE_RE = re.compile(r"[^A-Za-z0-9_-]+")


def _safe_q_id(raw: str) -> str:
    """Return a string safe to use as an HTML name/id attribute."""
    s = _Q_ID_SAFE_RE.sub("-", str(raw)).strip("-")
    return s or "q"


def _make_units_summary(course_root: Path) -> list[dict]:
    """Return one summary dict per unit: number, title, href, lesson_count, summary."""
    out: list[dict] = []
    content_root = course_root / "content"
    if not content_root.exists():
        return out
    for unit_folder in sorted(content_root.glob("unit-*")):
        if not unit_folder.is_dir():
            continue
        unit_yaml_path = unit_folder / "unit.yaml"
        if not unit_yaml_path.exists():
            continue
        raw = (yaml.safe_load(unit_yaml_path.read_text(encoding="utf-8")) or {}).get("unit", {})
        n = int(raw.get("number", 0) or 0)
        title = str(raw.get("title", unit_folder.name))
        outcomes = raw.get("learning_outcomes") or []
        summary = outcomes[0] if outcomes else ""
        lessons_dir = unit_folder / "lessons"
        lesson_count = len(list(lessons_dir.glob("*.md"))) if lessons_dir.exists() else 0
        out.append({
            "number": n,
            "title": title,
            "href": f"unit-{n}.html",
            "lesson_count": lesson_count,
            "summary": summary,
            "folder": unit_folder,
        })
    return sorted(out, key=lambda u: u["number"])


def render_unit_preview(unit_folder: Path, course_root: Optional[Path] = None) -> str:
    """Phase 18: render one unit page with hero, sidebar, lesson cards, KC, footer."""
    if course_root is None:
        course_root = unit_folder.parent.parent
    course_meta = _load_course_meta(course_root)
    unit = _load_unit(unit_folder)
    units_summary = _make_units_summary(course_root)
    final_data = _load_course_final(course_root)
    has_final = final_data is not None
    md = _make_md()

    # Lesson nav for sidebar. Anchor and lesson_id share the same value so the
    # gating script (which reads article ids from rendered HTML) and the
    # sidebar's data-lesson-id stay aligned, and so lesson identifiers are
    # unique across units.
    current_unit_lessons = []
    for i, lesson in enumerate(unit.lessons, 1):
        current_unit_lessons.append({
            "index": i,
            "title": lesson.title,
            "anchor": f"u{unit.number}-l{i}",
            "lesson_id": f"u{unit.number}-l{i}",
        })

    sidebar_html = render_sidebar(
        units=[{"number": u["number"], "title": u["title"], "href": u["href"]}
               for u in units_summary],
        current_unit_number=unit.number,
        current_unit_lessons=current_unit_lessons,
        has_final=has_final,
        course_slug=course_meta.course_slug,
    )

    hero_html = render_hero(
        course_name=unit.title,
        tagline=course_meta.tagline if not course_meta.tagline else "",
        cover_image_url=course_meta.cover_image_url or None,
        eyebrow=f"{course_meta.course_name} - Unit {unit.number}",
        compact=True,
    )

    # Lesson cards.
    lesson_cards = []
    for i, lesson in enumerate(unit.lessons, 1):
        expanded = _expand_microsim_directives(lesson.body_markdown, unit.number)
        body_html = _render_with_mermaid(md, expanded, demote_headings=True)
        anchor = f"u{unit.number}-l{i}"
        lesson_cards.append(
            render_lesson_card(
                unit_number=unit.number,
                lesson_index=i,
                lesson_title=lesson.title,
                body_html=body_html,
                anchor_id=anchor,
            )
        )
    lessons_block = "\n\n".join(lesson_cards) if lesson_cards else (
        '<p class="empty"><em>Lessons coming soon.</em></p>'
    )

    # Knowledge check (study or test).
    kc_mode = resolve_kc_mode(unit, course_meta)
    test_js = ""
    if unit.knowledge_check:
        if kc_mode == "test":
            kc_inner = render_test_section(
                unit.knowledge_check_data,
                section_id=f"unit-{unit.number}-kc-test",
                heading=unit.knowledge_check_title,
                course_slug=course_meta.course_slug,
                simple_mode=True,
                unit_number=unit.number,
            )
            kc_html = (
                '<section class="kc fade-in" id="kc">\n'
                + kc_inner
                + '\n</section>'
            )
            test_js = _TEST_MODE_JS
        else:
            kc_items = "\n".join(
                _render_question(i, q) for i, q in enumerate(unit.knowledge_check)
            )
            kc_html = (
                '<section class="kc fade-in" id="kc">\n'
                f'  <h2>{_esc(unit.knowledge_check_title)}</h2>\n'
                f'  <ol class="kc-list">\n{kc_items}\n  </ol>\n'
                '</section>'
            )
    else:
        kc_html = (
            '<section class="kc fade-in" id="kc">\n'
            f'  <h2>{_esc(unit.knowledge_check_title)}</h2>\n'
            '  <p><em>No knowledge check questions yet.</em></p>\n'
            '</section>'
        )

    footer_html = render_footer(
        course_name=course_meta.course_name,
        course_slug=course_meta.course_slug,
        logo_url=course_meta.logo_url or None,
        author_credit=course_meta.author_credit,
        license_text=course_meta.license_text or None,
        units=[{"number": u["number"], "title": u["title"], "href": u["href"]}
               for u in units_summary],
    )

    page_title = f"{course_meta.course_name} - Unit {unit.number}: {unit.title}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  {_render_head(page_title, course_meta.brand_secondary_color)}
</head>
<body id="top">
  {hero_html}
  <div class="page-shell with-sidebar">
    {sidebar_html}
    <main>
{lessons_block}

{kc_html}
    </main>
  </div>
  {footer_html}
  {_MERMAID_INIT}
  {test_js}
  {PROGRESS_AND_ANIMATION_JS}
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

# Phase 18: course CSS overrides moved into style.css alongside the
# polish styles. The constant remains as an empty string so any older
# string-formatted templates still using it keep rendering.
_COURSE_CSS_OVERRIDES = ""


_INTER_FONT_HEAD = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="https://fonts.googleapis.com/css2?'
    'family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">'
)


def _render_head(page_title: str, brand_secondary_color: str = "") -> str:
    """Common <head> contents: meta, title, fonts, style.css, Mermaid CDN.

    brand_secondary_color: optional hex color injected as a CSS variable
    override so courses can supply their own accent without editing
    style.css.
    """
    extra_root = ""
    if brand_secondary_color:
        extra_root = (
            f'<style>:root {{ --brand-2: {_esc(brand_secondary_color)}; }}</style>\n'
        )
    return (
        '<meta charset="UTF-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'  <title>{_esc(page_title)}</title>\n'
        f'  {_INTER_FONT_HEAD}\n'
        f'  <style>\n{_load_css()}</style>\n'
        f'  {extra_root}'
        f'  {_MERMAID_HEAD}'
    )


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
    """Phase 18: render the landing page (hero + unit-card grid + footer).

    The all-in-one single-page output of earlier phases is replaced by a
    multi-page bundle. This function returns the index.html body. Per-unit
    pages and the final page are rendered separately by render_unit_preview
    and render_final_preview; write_course_preview ties them together.
    """
    course_meta = _load_course_meta(course_root)
    units_summary = _make_units_summary(course_root)
    final_data = _load_course_final(course_root)
    has_final = final_data is not None

    page_title = f"{course_meta.course_name}"

    meta_items: list[str] = []
    n_units = len(units_summary)
    if n_units:
        meta_items.append(
            f"{n_units} unit" + ("s" if n_units != 1 else "")
        )
    if has_final:
        meta_items.append("Final assessment included")

    hero_html = render_hero(
        course_name=course_meta.course_name,
        tagline=course_meta.tagline,
        cover_image_url=course_meta.cover_image_url or None,
        eyebrow="Course",
        meta_items=meta_items or None,
    )

    cards_html = render_unit_card_grid([
        render_unit_card(
            unit_number=u["number"],
            unit_title=u["title"],
            summary=u["summary"],
            lesson_count=u["lesson_count"],
            href=u["href"],
            accent_index=u["number"],
        )
        for u in units_summary
    ])

    final_callout_html = ""
    if has_final:
        final_name = final_data.get("name") or "Course Final Assessment"
        final_callout_html = (
            '<section class="final-callout fade-in" '
            'style="margin-top:2.4em;padding:28px 32px;border:1px solid var(--rule);'
            'border-radius:var(--radius-md);background:var(--bg-soft);">\n'
            '  <h2 style="margin-top:0;">Course Final Assessment</h2>\n'
            f'  <p>{_esc(final_name)} is available once you have worked '
            'through the units.</p>\n'
            '  <a class="cta" href="final.html" '
            'style="display:inline-block;background:var(--brand);color:#fff;'
            'padding:12px 22px;border-radius:var(--radius-sm);'
            'text-decoration:none;font-weight:700;">Open the final assessment</a>\n'
            '</section>'
        )

    footer_html = render_footer(
        course_name=course_meta.course_name,
        course_slug=course_meta.course_slug,
        logo_url=course_meta.logo_url or None,
        author_credit=course_meta.author_credit,
        license_text=course_meta.license_text or None,
        units=[{"number": u["number"], "title": u["title"], "href": u["href"]}
               for u in units_summary],
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  {_render_head(page_title, course_meta.brand_secondary_color)}
</head>
<body id="top">
  {hero_html}
  <main class="page-shell">
    <section class="fade-in">
      <h2>Units</h2>
      {cards_html}
    </section>
    {final_callout_html}
  </main>
  {footer_html}
  {_MERMAID_INIT}
  {PROGRESS_AND_ANIMATION_JS}
</body>
</html>
"""


def write_course_preview(course_root: Path, output_dir: Path) -> Path:
    """Phase 18: write the multi-page bundle to output_dir.

    Files written:
      - index.html (landing: hero + unit cards + footer)
      - unit-N.html for each unit (hero + sidebar + lesson cards + KC + footer)
      - final.html (when exam/course-final.yaml exists)
      - unit-NN-microsims/ folders (copied from each unit's microsims/)

    The legacy single-file course-preview.html is removed if present, since
    index.html now serves the landing role.

    Returns the path to index.html (the natural deploy entry point).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Landing page.
    index_html = render_course_preview(course_root)
    index_path = output_dir / "index.html"
    index_path.write_text(index_html, encoding="utf-8")

    # Per-unit pages + microsim folder copies.
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

            unit_html = render_unit_preview(unit_folder, course_root)
            (output_dir / f"unit-{n}.html").write_text(unit_html, encoding="utf-8")

            microsims_src = unit_folder / "microsims"
            if microsims_src.exists() and microsims_src.is_dir():
                microsims_dst = output_dir / f"unit-{n:02d}-microsims"
                if microsims_dst.exists():
                    shutil.rmtree(microsims_dst)
                shutil.copytree(microsims_src, microsims_dst)

    # Final assessment page.
    final_yaml_path = course_root / "exam" / "course-final.yaml"
    if final_yaml_path.exists():
        final_html = render_final_preview(course_root)
        (output_dir / "final.html").write_text(final_html, encoding="utf-8")

    # Drop the legacy single-page output: index.html now owns the landing role.
    legacy = output_dir / "course-preview.html"
    if legacy.exists():
        legacy.unlink()

    return index_path


# --------------------------------------------------------------------------
# Standalone final preview: just the course final, in test mode.
# --------------------------------------------------------------------------

def render_final_preview(course_root: Path) -> str:
    """Render a polished page showing the course final assessment.

    Includes the hero, the sticky sidebar (so students can navigate back
    to units), the test section itself, and the branded footer. Used by
    write_course_preview to write final.html and by write_final_preview
    to write the legacy final-preview.html alias.
    """
    course_meta = _load_course_meta(course_root)
    final_data = _load_course_final(course_root)
    units_summary = _make_units_summary(course_root)
    final_name = (final_data or {}).get("name") or "Final Assessment"
    page_title = f"{course_meta.course_name} - Final Assessment"

    hero_html = render_hero(
        course_name="Course Final Assessment",
        tagline="",
        cover_image_url=course_meta.cover_image_url or None,
        eyebrow=course_meta.course_name,
        compact=True,
    )

    sidebar_html = render_sidebar(
        units=[{"number": u["number"], "title": u["title"], "href": u["href"]}
               for u in units_summary],
        current_unit_number=None,
        current_unit_lessons=None,
        has_final=True,
        course_slug=course_meta.course_slug,
    )

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
            course_slug=course_meta.course_slug,
        )
        test_js = _TEST_MODE_JS

    footer_html = render_footer(
        course_name=course_meta.course_name,
        course_slug=course_meta.course_slug,
        logo_url=course_meta.logo_url or None,
        author_credit=course_meta.author_credit,
        license_text=course_meta.license_text or None,
        units=[{"number": u["number"], "title": u["title"], "href": u["href"]}
               for u in units_summary],
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  {_render_head(page_title, course_meta.brand_secondary_color)}
</head>
<body id="top">
  {hero_html}
  <div class="page-shell with-sidebar">
    {sidebar_html}
    <main>
      {body_html}
    </main>
  </div>
  {footer_html}
  {test_js}
  {PROGRESS_AND_ANIMATION_JS}
</body>
</html>
"""


def write_final_preview(course_root: Path, output_dir: Path) -> Path:
    """Render the standalone final preview to output_dir/final-preview.html.

    Legacy alias for `bes preview-final`. Same body as final.html written
    by write_course_preview, but under the older filename.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    html = render_final_preview(course_root)
    out_path = output_dir / "final-preview.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path
