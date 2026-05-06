"""Course gating skill: apply, dry-run, and remove modes.

Reads a generated static-web course site, discovers unit pages, lesson IDs,
and quiz storage keys, then writes gating.js and gating.css and patches the
HTML files to wire everything up.

Path A: standalone post-processor. The hook for merging into the generator
later is documented in SKILL.md.
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional

import yaml


SCRIPT_TAG = '<script src="assets/gating.js" defer></script>'
LINK_TAG = '<link rel="stylesheet" href="assets/gating.css">'
WRAPPER_OPEN = '<div id="gated-content">'
WRAPPER_CLOSE = '</div><!-- /#gated-content -->'

# Markers we use to cleanly identify our injections for idempotent re-runs
INJECT_BEGIN = '<!-- COURSE-GATING:BEGIN -->'
INJECT_END = '<!-- COURSE-GATING:END -->'


class GatingError(Exception):
    """Raised when gating cannot proceed."""


def find_course_root(start: Optional[Path] = None) -> Optional[Path]:
    """Walk up from start (or cwd) to find course-config.yaml."""
    if start is None:
        start = Path.cwd()
    current = Path(start).resolve()
    while True:
        if (current / "course-config.yaml").exists():
            return current
        if current.parent == current:
            return None
        current = current.parent


def load_course_slug(course_root: Path) -> str:
    """Read course-config.yaml and return the slug."""
    config_file = course_root / "course-config.yaml"
    with config_file.open() as f:
        data = yaml.safe_load(f) or {}
    course = data.get("course") or {}
    slug = course.get("slug")
    if not slug:
        raise GatingError("course-config.yaml is missing a slug.")
    return slug


def discover_unit_pages(site_root: Path) -> list[Path]:
    """Find all unit-N.html files in site_root, sorted by unit number."""
    pages = []
    for f in site_root.iterdir():
        m = re.match(r"^unit-(\d+)\.html$", f.name)
        if m:
            pages.append((int(m.group(1)), f))
    pages.sort(key=lambda x: x[0])
    return [p for _, p in pages]


def parse_unit_page(unit_html: Path) -> dict:
    """Extract lesson IDs and KC storage key from a unit page."""
    text = unit_html.read_text(encoding="utf-8")

    # Find lesson card IDs
    lesson_ids = re.findall(
        r'<article[^>]*\bclass="[^"]*\blesson-card\b[^"]*"[^>]*\bid="([^"]+)"',
        text,
    )
    if not lesson_ids:
        # Try alternate attribute order
        lesson_ids = re.findall(
            r'<article[^>]*\bid="([^"]+)"[^>]*\bclass="[^"]*\blesson-card\b[^"]*"',
            text,
        )

    # Find the KC test-section's storage key
    kc_key = None
    kc_threshold = None
    section_match = re.search(
        r'<section[^>]*\bclass="[^"]*\btest-section\b[^"]*"[^>]*>',
        text,
    )
    if section_match:
        section_tag = section_match.group(0)
        key_m = re.search(r'data-storage-key="([^"]+)"', section_tag)
        if key_m:
            kc_key = key_m.group(1)
        threshold_m = re.search(r'data-pass-threshold="([^"]+)"', section_tag)
        if threshold_m:
            try:
                kc_threshold = float(threshold_m.group(1))
            except ValueError:
                kc_threshold = None

    # Extract unit number from filename
    m = re.match(r"^unit-(\d+)\.html$", unit_html.name)
    unit_number = int(m.group(1)) if m else None

    return {
        "number": unit_number,
        "lessonIds": lesson_ids,
        "kcStorageKey": kc_key,
        "kcThreshold": kc_threshold,
    }


def parse_final_page(final_html: Path) -> dict:
    """Extract storage key and threshold from final.html."""
    text = final_html.read_text(encoding="utf-8")
    section_match = re.search(
        r'<section[^>]*\bclass="[^"]*\btest-section\b[^"]*"[^>]*>',
        text,
    )
    info = {"storageKey": None, "threshold": None}
    if section_match:
        section_tag = section_match.group(0)
        key_m = re.search(r'data-storage-key="([^"]+)"', section_tag)
        if key_m:
            info["storageKey"] = key_m.group(1)
        threshold_m = re.search(r'data-pass-threshold="([^"]+)"', section_tag)
        if threshold_m:
            try:
                info["threshold"] = float(threshold_m.group(1))
            except ValueError:
                pass
    return info


def build_config(course_slug: str, units: list[dict], final_info: Optional[dict],
                  require_quiz_pass: bool = True) -> dict:
    """Build the CONFIG object that gets injected into gating.js."""
    return {
        "courseSlug": course_slug,
        "requireQuizPass": require_quiz_pass,
        "units": [
            {
                "number": u["number"],
                "lessonIds": u["lessonIds"],
                "kcStorageKey": u["kcStorageKey"],
            }
            for u in units
        ],
        "final": (
            {"storageKey": final_info["storageKey"]}
            if final_info and final_info.get("storageKey")
            else None
        ),
    }


def render_gating_js(template: str, config: dict) -> str:
    """Inject the CONFIG object into the JS template."""
    config_json = json.dumps(config, indent=2)
    return template.replace("/* CONFIG_INJECTED */", config_json)


def patch_html_head(text: str, course_root: Path) -> tuple[str, bool]:
    """Add the gating CSS link to the <head>. Returns (new_text, changed)."""
    if LINK_TAG in text:
        return text, False
    head_close = re.search(r"</head>", text)
    if not head_close:
        return text, False
    inject = f"  {INJECT_BEGIN}\n  {LINK_TAG}\n  {INJECT_END}\n"
    new_text = text[:head_close.start()] + inject + text[head_close.start():]
    return new_text, True


def patch_html_body_script(text: str) -> tuple[str, bool]:
    """Add the gating script tag before </body>. Returns (new_text, changed)."""
    if SCRIPT_TAG in text:
        return text, False
    body_close = re.search(r"</body>", text)
    if not body_close:
        return text, False
    inject = f"  {INJECT_BEGIN}\n  {SCRIPT_TAG}\n  {INJECT_END}\n"
    new_text = text[:body_close.start()] + inject + text[body_close.start():]
    return new_text, True


def wrap_main_content(text: str) -> tuple[str, bool]:
    """Wrap <main>...</main> contents in <div id="gated-content">...</div>.

    Returns (new_text, changed).
    """
    if 'id="gated-content"' in text:
        return text, False

    main_open = re.search(r'<main[^>]*>', text)
    main_close = re.search(r'</main>', text)
    if not main_open or not main_close:
        return text, False

    # Insert wrapper open right after <main ...>
    open_end = main_open.end()
    close_start = main_close.start()

    new_text = (
        text[:open_end]
        + f"\n    {INJECT_BEGIN}\n    {WRAPPER_OPEN}\n"
        + text[open_end:close_start]
        + f"\n    {WRAPPER_CLOSE}\n    {INJECT_END}\n  "
        + text[close_start:]
    )
    return new_text, True


def add_unit_card_attrs(text: str) -> tuple[str, int]:
    """Add data-unit-number to each .unit-card on the index. Returns (new_text, n_added)."""
    # Match unit cards that link to unit-N.html
    pattern = re.compile(
        r'(<a[^>]*\bclass="[^"]*\bunit-card\b[^"]*"[^>]*\bhref="unit-(\d+)\.html"[^>]*)(>)',
    )
    n_added = 0

    def replace(m):
        nonlocal n_added
        attrs = m.group(1)
        unit_n = m.group(2)
        if 'data-unit-number=' in attrs:
            return m.group(0)
        n_added += 1
        return f'{attrs} data-unit-number="{unit_n}"{m.group(3)}'

    new_text = pattern.sub(replace, text)

    # Also try the alternate order (href before class)
    pattern2 = re.compile(
        r'(<a[^>]*\bhref="unit-(\d+)\.html"[^>]*\bclass="[^"]*\bunit-card\b[^"]*)(>)',
    )

    def replace2(m):
        nonlocal n_added
        attrs = m.group(1)
        unit_n = m.group(2)
        if 'data-unit-number=' in attrs:
            return m.group(0)
        n_added += 1
        return f'{attrs} data-unit-number="{unit_n}"{m.group(3)}'

    new_text = pattern2.sub(replace2, new_text)
    return new_text, n_added


def remove_injections(text: str) -> str:
    """Strip all COURSE-GATING marker blocks. Used in remove mode."""
    pattern = re.compile(
        re.escape(INJECT_BEGIN) + r'.*?' + re.escape(INJECT_END),
        re.DOTALL,
    )
    return pattern.sub('', text)


def apply_gating(course_root: Path, site_root: Path,
                  require_quiz_pass: bool = True,
                  dry_run: bool = False) -> dict:
    """Apply gating to the site. Returns a summary dict."""
    if not site_root.exists():
        raise GatingError(f"site_root {site_root} does not exist.")

    course_slug = load_course_slug(course_root)
    unit_pages = discover_unit_pages(site_root)
    if not unit_pages:
        raise GatingError(f"No unit-N.html files found in {site_root}.")

    final_html = site_root / "final.html"
    has_final = final_html.exists()

    # Discover unit metadata
    units = [parse_unit_page(p) for p in unit_pages]
    warnings = []
    for u in units:
        if not u["lessonIds"]:
            warnings.append(f"Unit {u['number']} has no lesson-card elements with IDs")
        if not u["kcStorageKey"]:
            warnings.append(f"Unit {u['number']} has no test-section with data-storage-key")

    final_info = parse_final_page(final_html) if has_final else None
    if has_final and not (final_info and final_info.get("storageKey")):
        warnings.append("final.html exists but has no test-section with data-storage-key")

    # Build CONFIG object and JS file
    config = build_config(course_slug, units, final_info, require_quiz_pass)

    skill_dir = Path(__file__).parent.parent
    js_template = (skill_dir / "templates" / "gating.js.template").read_text(encoding="utf-8")
    css_template = (skill_dir / "templates" / "gating.css.template").read_text(encoding="utf-8")

    js_output = render_gating_js(js_template, config)

    summary = {
        "files_written": [],
        "files_modified": [],
        "warnings": warnings,
        "units_gated": len([u for u in units if u["number"] > 1]),
        "final_gated": has_final,
        "dry_run": dry_run,
    }

    # Write the JS and CSS
    assets_dir = site_root / "assets"
    if not dry_run:
        assets_dir.mkdir(exist_ok=True)
        (assets_dir / "gating.js").write_text(js_output, encoding="utf-8")
        (assets_dir / "gating.css").write_text(css_template, encoding="utf-8")
    summary["files_written"].append(str(assets_dir / "gating.js"))
    summary["files_written"].append(str(assets_dir / "gating.css"))

    # Patch HTML files
    pages_to_patch = [site_root / "index.html"] + unit_pages
    if has_final:
        pages_to_patch.append(final_html)

    for page in pages_to_patch:
        if not page.exists():
            continue

        text = page.read_text(encoding="utf-8")
        original = text
        is_index = page.name == "index.html"

        # 1. Add CSS link in head
        text, _ = patch_html_head(text, course_root)

        # 2. Add script tag before </body>
        text, _ = patch_html_body_script(text)

        # 3. Wrap main content (skip for index, gating just adds card classes there)
        if not is_index:
            text, _ = wrap_main_content(text)
        else:
            # Add data-unit-number to unit cards
            text, _ = add_unit_card_attrs(text)

        if text != original:
            summary["files_modified"].append(str(page))
            if not dry_run:
                page.write_text(text, encoding="utf-8")

    return summary


def remove_gating(site_root: Path, dry_run: bool = False) -> dict:
    """Remove all gating from the site."""
    if not site_root.exists():
        raise GatingError(f"site_root {site_root} does not exist.")

    summary = {
        "files_removed": [],
        "files_modified": [],
        "dry_run": dry_run,
    }

    # Remove gating.js and gating.css
    for fname in ("gating.js", "gating.css"):
        f = site_root / "assets" / fname
        if f.exists():
            summary["files_removed"].append(str(f))
            if not dry_run:
                f.unlink()

    # Strip injection markers from all HTML files
    for html_file in site_root.glob("*.html"):
        text = html_file.read_text(encoding="utf-8")
        new_text = remove_injections(text)
        if new_text != text:
            summary["files_modified"].append(str(html_file))
            if not dry_run:
                html_file.write_text(new_text, encoding="utf-8")

    return summary


def print_summary(summary: dict, mode: str):
    """Print a console summary of what happened."""
    prefix = "[DRY RUN] " if summary.get("dry_run") else ""
    print()
    print(f"{prefix}Course gating: {mode}")
    print()
    if summary.get("files_written"):
        print(f"Files written ({len(summary['files_written'])}):")
        for f in summary["files_written"]:
            print(f"  + {f}")
    if summary.get("files_modified"):
        print(f"Files modified ({len(summary['files_modified'])}):")
        for f in summary["files_modified"]:
            print(f"  ~ {f}")
    if summary.get("files_removed"):
        print(f"Files removed ({len(summary['files_removed'])}):")
        for f in summary["files_removed"]:
            print(f"  - {f}")
    if "units_gated" in summary:
        print(f"Units gated: {summary['units_gated']}")
        print(f"Final gated: {'yes' if summary.get('final_gated') else 'no'}")
    if summary.get("warnings"):
        print()
        print(f"Warnings ({len(summary['warnings'])}):")
        for w in summary["warnings"]:
            print(f"  ! {w}")
    print()


def main():
    """CLI entry point. Args: --site PATH [--dry-run | --remove] [--no-quiz-required]"""
    import argparse

    parser = argparse.ArgumentParser(description="Course gating skill")
    parser.add_argument("--site", required=True, help="Site root (where the static-web output lives)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change, but don't write")
    parser.add_argument("--remove", action="store_true", help="Remove gating instead of applying")
    parser.add_argument("--no-quiz-required", action="store_true",
                        help="Lessons-viewed-only gate (skip the KC pass requirement)")
    args = parser.parse_args()

    course_root = find_course_root()
    if course_root is None:
        print("Error: course-config.yaml not found. Are you inside a course repo?",
              file=sys.stderr)
        sys.exit(1)

    site_root = Path(args.site).resolve()

    try:
        if args.remove:
            summary = remove_gating(site_root, dry_run=args.dry_run)
            print_summary(summary, "remove")
        else:
            summary = apply_gating(
                course_root=course_root,
                site_root=site_root,
                require_quiz_pass=not args.no_quiz_required,
                dry_run=args.dry_run,
            )
            print_summary(summary, "apply")
    except GatingError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
