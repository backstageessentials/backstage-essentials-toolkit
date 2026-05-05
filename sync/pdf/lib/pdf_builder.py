"""Main PDF sync entry points.

Two callable shapes match the Phase 11/12 architecture:

- `sync(...)`: invoked by `bes sync` when course-config.yaml has
  `platform: pdf`. Same signature as the Thinkific and Canvas sync skills
  so the platform router can dispatch uniformly.
- `export_pdf(...)`: invoked by `bes export-pdf` regardless of the
  course's primary platform. Generates a PDF without changing platform.

Both call into the same `_render(...)` core. The flow is:

  1. Resolve course config (page size, microsim strategy, include_final).
  2. Build the HTML document via layout.build_html_document.
  3. Render to PDF via WeasyPrint. If WeasyPrint cannot import (missing
     system libs like Pango on a fresh Mac), fall back to Chrome
     headless. If neither is available, emit a clear error.
  4. Write the PDF to build/pdf/<slug>.pdf and the intermediate HTML to
     build/pdf/<slug>.html for inspection and as the input the renderer
     consumed.

Build time grows with the number of Mermaid diagrams (each shells out to
mmdc). The cache at .mermaid-svg-cache/ prevents re-rendering on
incremental builds.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from .layout import build_html_document

logger = logging.getLogger(__name__)


_DEFAULT_OUTPUT_DIR = "build/pdf"


class PDFBuildError(Exception):
    """Raised when neither WeasyPrint nor Chrome headless can render the PDF."""


def _ensure_macos_dylib_path() -> None:
    # Homebrew installs Pango/Cairo/etc. under /opt/homebrew/lib (Apple Silicon)
    # or /usr/local/lib (Intel). macOS's dynamic linker does not search these by
    # default, so WeasyPrint's cffi dlopen calls fail with "no such file" even
    # when the libs are present. Prepend Homebrew's lib dir so the import works
    # without users having to set DYLD_FALLBACK_LIBRARY_PATH themselves.
    if sys.platform != "darwin":
        return
    candidates = ["/opt/homebrew/lib", "/usr/local/lib"]
    existing = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    parts = [p for p in existing.split(":") if p]
    for candidate in candidates:
        if Path(candidate, "libgobject-2.0.dylib").exists() and candidate not in parts:
            parts.insert(0, candidate)
    if parts:
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(parts)


def _try_weasyprint(html_str: str, base_url: Path, output_path: Path) -> str:
    """Render with WeasyPrint. Returns 'weasyprint' on success, None on import failure.

    Raises any other exception from WeasyPrint (e.g., CSS parse errors).
    """
    _ensure_macos_dylib_path()
    try:
        from weasyprint import HTML  # type: ignore
    except (ImportError, OSError) as e:
        logger.info(f"WeasyPrint unavailable: {e}")
        return None
    HTML(string=html_str, base_url=str(base_url)).write_pdf(str(output_path))
    return "weasyprint"


def _try_chrome_headless(html_path: Path, output_path: Path) -> Optional[str]:
    """Render via Chrome headless. Returns 'chrome' on success, None if no Chrome."""
    chrome = _find_chrome()
    if not chrome:
        return None
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={output_path}",
        f"file://{html_path}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        logger.warning(f"Chrome headless failed: {result.stderr[:500]}")
        return None
    return "chrome"


def _find_chrome() -> Optional[str]:
    candidates = [
        os.environ.get("CHROME_PATH"),
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chrome"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


def _render(course_root: Path, output_dir: Optional[Path] = None,
             dry_run: bool = False) -> int:
    """Build and render the PDF. Returns exit code (0 success, 1 failure)."""
    if not (course_root / "course-config.yaml").exists():
        print(f"  Missing course-config.yaml in {course_root}")
        return 1

    if output_dir is None:
        output_dir = course_root / _DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    mermaid_cache = course_root / ".mermaid-svg-cache"
    screenshot_dir = course_root / "microsim-screenshots"
    if not screenshot_dir.exists():
        screenshot_dir = None

    print("[1/4] Building HTML document...")
    start = time.time()
    html_str, course = build_html_document(
        course_root=course_root,
        mermaid_cache=mermaid_cache,
        screenshot_dir=screenshot_dir,
    )
    print(f"  OK ({course.name}, page size {course.page_size}, "
          f"microsims via {course.microsim_strategy})")

    html_path = output_dir / f"{course.slug}.html"
    pdf_path = output_dir / f"{course.slug}.pdf"
    html_path.write_text(html_str, encoding="utf-8")
    print(f"  Intermediate HTML: {html_path.relative_to(course_root)}")

    if dry_run:
        print("[2/4] (skipped in dry run)")
        print("[3/4] (skipped in dry run)")
        print("[4/4] Dry run complete.")
        print(f"  HTML written, no PDF generated. Inspect "
              f"{html_path.relative_to(course_root)} to verify content.")
        return 0

    print("[2/4] Rendering PDF (trying WeasyPrint)...")
    renderer = None
    try:
        renderer = _try_weasyprint(html_str, course_root, pdf_path)
    except Exception as e:
        print(f"  WeasyPrint raised an error: {e}")
        renderer = None

    if renderer is None:
        print("  WeasyPrint not available, trying Chrome headless...")
        renderer = _try_chrome_headless(html_path, pdf_path)

    if renderer is None:
        print()
        print("[red]No PDF renderer worked.[/red]")
        print()
        print("Install one of:")
        print("  WeasyPrint, recommended:")
        print("    pip install weasyprint")
        print("    brew install pango libffi  (macOS, for the system libs)")
        print()
        print("  Chrome / Chromium (no setup needed if Chrome is already installed)")
        print()
        print(f"The intermediate HTML is at {html_path}; open it in any browser")
        print("to inspect the layout while you set up a renderer.")
        return 1

    print(f"  OK (rendered with {renderer})")

    print("[3/4] Verifying output...")
    if not pdf_path.exists() or pdf_path.stat().st_size < 1024:
        print(f"  PDF appears truncated or empty: {pdf_path}")
        return 1
    size_kb = pdf_path.stat().st_size / 1024
    print(f"  OK ({size_kb:.1f} KB)")

    print("[4/4] Done!")
    elapsed = time.time() - start
    print()
    print("Summary:")
    print(f"  Course:    {course.name}")
    print(f"  Output:    {pdf_path}")
    print(f"  Renderer:  {renderer}")
    print(f"  Page size: {course.page_size}")
    print(f"  Time:      {elapsed:.1f} seconds")
    return 0


# ---- Public entry points ----

def sync(course_root: Path = None, dry_run: bool = False,
         force_update: bool = False,
         units_to_sync: Optional[list[int]] = None) -> int:
    """Entry point matching the Thinkific/Canvas sync signature.

    `force_update` and `units_to_sync` are accepted for signature
    compatibility with the platform router but do not change PDF output:
    a PDF is always generated whole. They are recorded in the log for
    transparency.
    """
    if course_root is None:
        course_root = Path.cwd()
    course_root = Path(course_root).resolve()
    print(f"[pdf sync] course_root={course_root}")
    if force_update or units_to_sync:
        print("  (--force and --units have no effect for PDF; the PDF is always "
              "generated as a whole document)")
    return _render(course_root=course_root, dry_run=dry_run)


def export_pdf(course_root: Path = None, dry_run: bool = False,
                output_dir: Optional[Path] = None) -> int:
    """Entry point for `bes export-pdf` (regardless of primary platform)."""
    if course_root is None:
        course_root = Path.cwd()
    course_root = Path(course_root).resolve()
    print(f"[pdf export] course_root={course_root}")
    return _render(course_root=course_root, output_dir=output_dir, dry_run=dry_run)
