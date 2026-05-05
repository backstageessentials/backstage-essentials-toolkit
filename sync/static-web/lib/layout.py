"""Layout helpers for static-web Phase 18 visual polish.

These functions compose HTML for the hero banner, unit-card grid,
lesson cards, sticky sidebar, and branded footer. preview.py imports
them to assemble pages without inlining a giant block of f-strings
per page.

Each helper returns a ready-to-embed HTML string. None of them apply
markdown or Mermaid rewrites; preview.py handles that and passes
already-rendered HTML where lesson bodies are needed.
"""

from datetime import datetime, timezone
from html import escape as _esc
from typing import Optional


# ---- icons (inline SVG, currentColor) -------------------------------------

_ICON_DOC = (
    '<svg class="lesson-icon" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M6 2h8l4 4v16H6V2zm8 0v6h6"'
    ' fill="none" stroke="currentColor" stroke-width="2"'
    ' stroke-linejoin="round"/></svg>'
)
_ICON_VIDEO = (
    '<svg class="lesson-icon" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M3 6h12v12H3zM15 10l5-3v10l-5-3z"'
    ' fill="none" stroke="currentColor" stroke-width="2"'
    ' stroke-linejoin="round"/></svg>'
)
_ICON_INTERACTIVE = (
    '<svg class="lesson-icon" viewBox="0 0 24 24" aria-hidden="true">'
    '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/>'
    '<path d="M8 12l3 3 5-6" fill="none" stroke="currentColor" stroke-width="2"'
    ' stroke-linecap="round" stroke-linejoin="round"/></svg>'
)


def _word_count(text: str) -> int:
    """Rough word count. Strips HTML tags before counting."""
    if not text:
        return 0
    import re
    plain = re.sub(r"<[^>]+>", " ", text)
    return len([w for w in plain.split() if w.strip()])


def reading_time_minutes(text: str, wpm: int = 200) -> int:
    """Words per minute -> minutes, rounded up; minimum 1."""
    n = _word_count(text)
    if n == 0:
        return 1
    return max(1, -(-n // wpm))  # ceil division


# ---- hero -----------------------------------------------------------------

def render_hero(course_name: str, tagline: str = "",
                 cover_image_url: Optional[str] = None,
                 eyebrow: Optional[str] = None,
                 compact: bool = False,
                 meta_items: Optional[list[str]] = None) -> str:
    """Hero banner. Used at the top of index.html, unit pages, and final.html.

    cover_image_url: if provided, layered under the gradient as a background.
    eyebrow: small uppercase label above the title (e.g., "Unit 3").
    compact: tighter padding + smaller h1; tagline hidden. Used on unit pages.
    meta_items: small inline strings displayed under the tagline (e.g.,
                "6 units", "12 hours self-paced").
    """
    classes = ["hero"]
    if cover_image_url:
        classes.append("has-cover")
    if compact:
        classes.append("compact")

    inline_style = ""
    if cover_image_url:
        inline_style = f' style="--cover-image: url(\'{_esc(cover_image_url, quote=True)}\');"'

    eyebrow_html = (
        f'<p class="hero-eyebrow">{_esc(eyebrow)}</p>' if eyebrow else ""
    )
    tagline_html = (
        f'<p class="hero-tagline">{_esc(tagline)}</p>' if tagline else ""
    )

    meta_html = ""
    if meta_items:
        items = []
        for it in meta_items:
            items.append(f'<span class="meta-item">{_esc(it)}</span>')
        meta_html = (
            f'<div class="hero-meta">{"<span class=\"dot\"></span>".join(items)}</div>'
        )

    return (
        f'<header class="{" ".join(classes)}"{inline_style}>\n'
        f'  <div class="hero-inner">\n'
        f'    {eyebrow_html}\n'
        f'    <h1>{_esc(course_name)}</h1>\n'
        f'    {tagline_html}\n'
        f'    {meta_html}\n'
        f'  </div>\n'
        f'</header>'
    )


# ---- unit card grid -------------------------------------------------------

_ACCENT_CLASSES = ["", "accent-2", "accent-3", "accent-4"]


def render_unit_card(unit_number: int, unit_title: str,
                      summary: str, lesson_count: int,
                      href: str, accent_index: int = 0) -> str:
    accent = _ACCENT_CLASSES[accent_index % len(_ACCENT_CLASSES)]
    cls = f"unit-card {accent}".strip()
    summary_html = (
        f'<p class="unit-summary">{_esc(summary)}</p>'
        if summary else
        '<p class="unit-summary">&nbsp;</p>'
    )
    lessons_label = "lesson" if lesson_count == 1 else "lessons"
    return (
        f'<a class="{cls}" href="{_esc(href, quote=True)}">\n'
        f'  <p class="unit-number">Unit {unit_number}</p>\n'
        f'  <h3>{_esc(unit_title)}</h3>\n'
        f'  {summary_html}\n'
        f'  <p class="unit-meta">'
        f'<strong>{lesson_count}</strong> {lessons_label}'
        f'</p>\n'
        f'</a>'
    )


def render_unit_card_grid(cards: list[str]) -> str:
    if not cards:
        return '<p class="empty"><em>No units found in this course.</em></p>'
    return f'<div class="unit-grid">\n  ' + "\n  ".join(cards) + "\n</div>"


# ---- lesson cards ---------------------------------------------------------

def render_lesson_card(unit_number: int, lesson_index: int,
                        lesson_title: str, body_html: str,
                        anchor_id: str) -> str:
    minutes = reading_time_minutes(body_html)
    icon = _ICON_DOC
    lower_body = body_html.lower()
    if "<iframe" in lower_body:
        icon = _ICON_INTERACTIVE
    elif "<video" in lower_body or "youtube.com" in lower_body or "vimeo.com" in lower_body:
        icon = _ICON_VIDEO

    return (
        f'<article class="lesson-card fade-in" id="{_esc(anchor_id, quote=True)}">\n'
        f'  <div class="lesson-card-header">\n'
        f'    <div>\n'
        f'      <p class="lesson-number">Unit {unit_number} - Lesson {lesson_index}</p>\n'
        f'      <h3>{_esc(lesson_title)}</h3>\n'
        f'    </div>\n'
        f'    <span class="lesson-meta">{icon}{minutes} min read</span>\n'
        f'  </div>\n'
        f'  <div class="lesson-body">\n'
        f'{body_html}\n'
        f'  </div>\n'
        f'</article>'
    )


# ---- sidebar --------------------------------------------------------------

def render_sidebar(units: list[dict], current_unit_number: Optional[int] = None,
                    current_unit_lessons: Optional[list[dict]] = None,
                    has_final: bool = False,
                    course_slug: str = "") -> str:
    """Sticky sidebar with unit list + lesson list for the current unit.

    units: list of {"number", "title", "href"} dicts.
    current_unit_lessons: list of {"index", "title", "anchor", "lesson_id"}
                          dicts for the unit being viewed (lesson nav).
    """
    unit_items: list[str] = []
    for u in units:
        cls = "current" if u.get("number") == current_unit_number else ""
        unit_items.append(
            f'<li><a class="{cls}" '
            f'href="{_esc(u["href"], quote=True)}">'
            f'Unit {u["number"]}: {_esc(u["title"])}</a></li>'
        )
    units_html = "\n      ".join(unit_items)

    lesson_section = ""
    if current_unit_lessons:
        lesson_items = []
        for lesson in current_unit_lessons:
            lesson_items.append(
                f'<li><a data-lesson-id="{_esc(lesson["lesson_id"], quote=True)}" '
                f'href="#{_esc(lesson["anchor"], quote=True)}">'
                f'{lesson["index"]}. {_esc(lesson["title"])}</a></li>'
            )
        lessons_html = "\n      ".join(lesson_items)
        kc_link = (
            f'\n      <li><a href="#kc">Knowledge Check</a></li>'
        )
        lesson_section = (
            f'  <h4>Lessons</h4>\n'
            f'  <ul>\n      {lessons_html}{kc_link}\n  </ul>\n'
        )

    final_section = ""
    if has_final:
        final_section = (
            f'  <h4>Final</h4>\n'
            f'  <ul>\n'
            f'    <li><a href="final.html">Course Final Assessment</a></li>\n'
            f'  </ul>\n'
        )

    return (
        f'<button class="sidebar-toggle" aria-label="Toggle navigation" '
        f'aria-expanded="false">&#9776;</button>\n'
        f'<aside class="sidebar" data-course-slug="{_esc(course_slug, quote=True)}">\n'
        f'  <h4>Course</h4>\n'
        f'  <ul>\n'
        f'    <li><a href="index.html">Overview</a></li>\n'
        f'  </ul>\n'
        f'  <h4>Units</h4>\n'
        f'  <ul>\n      {units_html}\n  </ul>\n'
        f'{lesson_section}'
        f'{final_section}'
        f'</aside>'
    )


# ---- footer ---------------------------------------------------------------

def render_footer(course_name: str, course_slug: str = "",
                   logo_url: Optional[str] = None,
                   author_credit: str = "Backstage Essentials LLC",
                   license_text: Optional[str] = None,
                   include_unit_links: bool = True,
                   units: Optional[list[dict]] = None) -> str:
    year = datetime.now(timezone.utc).year
    logo_html = ""
    if logo_url:
        logo_html = (
            f'<img src="{_esc(logo_url, quote=True)}" '
            f'alt="{_esc(course_name)} logo">'
        )
    license_html = ""
    if license_text:
        license_html = (
            f'<p class="footer-license">{_esc(license_text)}</p>'
        )

    quick_links = [
        '<a href="#top">Back to top</a>',
        '<a href="index.html">Course home</a>',
    ]
    if include_unit_links and units:
        # Just point at index; the unit grid lives there. Could expand later.
        pass

    links_html = "\n      ".join(quick_links)
    return (
        f'<footer class="site-footer">\n'
        f'  <div class="footer-inner">\n'
        f'    <div class="footer-brand">\n'
        f'      {logo_html}\n'
        f'      <span>{_esc(course_name)} &middot; '
        f'{_esc(author_credit)} &middot; &copy; {year}</span>\n'
        f'    </div>\n'
        f'    <nav class="footer-links">\n'
        f'      {links_html}\n'
        f'    </nav>\n'
        f'  </div>\n'
        f'  {license_html}\n'
        f'</footer>'
    )


# ---- progress / animation JS ---------------------------------------------

PROGRESS_AND_ANIMATION_JS = """
<script>
(function () {
  // Sidebar mobile toggle
  var sb = document.querySelector('.sidebar');
  var btn = document.querySelector('.sidebar-toggle');
  if (sb && btn) {
    btn.addEventListener('click', function () {
      var open = sb.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // Reduced motion: if set, mark everything visible immediately and skip
  // observers entirely.
  var reducedMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reducedMotion) {
    document.querySelectorAll('.fade-in').forEach(function (el) {
      el.classList.add('visible');
    });
    document.querySelectorAll('.mermaid-wrap').forEach(function (el) {
      el.classList.add('ready');
    });
  } else if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.05 });
    document.querySelectorAll('.fade-in').forEach(function (el) {
      io.observe(el);
    });
    // Mermaid: fade in once the SVG is rendered.
    setTimeout(function () {
      document.querySelectorAll('.mermaid-wrap').forEach(function (el) {
        el.classList.add('ready');
      });
    }, 800);
  } else {
    // Old browser: just show everything.
    document.querySelectorAll('.fade-in').forEach(function (el) {
      el.classList.add('visible');
    });
    document.querySelectorAll('.mermaid-wrap').forEach(function (el) {
      el.classList.add('ready');
    });
  }

  // Progress: track which lessons have been viewed (via Intersection
  // Observer or scroll), persist in localStorage, mark sidebar links.
  var slug = (sb && sb.dataset.courseSlug) || '';
  var storageKey = slug ? ('course-' + slug + '-viewed-lessons') : '';
  var viewed = {};
  if (storageKey) {
    try {
      var raw = window.localStorage.getItem(storageKey);
      if (raw) {
        JSON.parse(raw).forEach(function (id) { viewed[id] = true; });
      }
    } catch (e) {}
  }
  function markViewed(id) {
    if (!id || viewed[id]) return;
    viewed[id] = true;
    if (storageKey) {
      try {
        window.localStorage.setItem(
          storageKey, JSON.stringify(Object.keys(viewed))
        );
      } catch (e) {}
    }
    var link = document.querySelector(
      '.sidebar a[data-lesson-id="' + id + '"]'
    );
    if (link) link.classList.add('viewed');
  }
  // Apply previously-viewed marks immediately.
  Object.keys(viewed).forEach(function (id) {
    var link = document.querySelector(
      '.sidebar a[data-lesson-id="' + id + '"]'
    );
    if (link) link.classList.add('viewed');
  });
  // Mark current unit's lessons as viewed when scrolled into view.
  if ('IntersectionObserver' in window) {
    var lessonObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting && entry.intersectionRatio > 0.3) {
          markViewed(entry.target.id);
        }
      });
    }, { threshold: 0.3 });
    document.querySelectorAll('article.lesson-card[id]').forEach(function (el) {
      lessonObserver.observe(el);
    });
  }

  // Sidebar lesson active highlight on scroll-spy.
  if ('IntersectionObserver' in window) {
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          document.querySelectorAll('.sidebar a.active').forEach(function (a) {
            a.classList.remove('active');
          });
          var link = document.querySelector(
            '.sidebar a[href="#' + entry.target.id + '"]'
          );
          if (link) link.classList.add('active');
        }
      });
    }, { rootMargin: '-30% 0px -55% 0px', threshold: 0 });
    document.querySelectorAll('article.lesson-card[id]').forEach(function (el) {
      spy.observe(el);
    });
  }
})();
</script>
"""
