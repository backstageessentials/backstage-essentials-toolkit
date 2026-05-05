"""Course configuration loader.

Finds and loads course-config.yaml from the current working directory. Used
by every bes command that needs to know which course to operate on.
"""

from pathlib import Path
from typing import Optional

import yaml


class ConfigError(Exception):
    """Raised when course-config.yaml is missing, unparseable, or incomplete."""


def find_course_root(start: Path = None) -> Optional[Path]:
    """Walk up from the start path until we find a course-config.yaml.

    Returns the folder containing course-config.yaml, or None if none found.
    """
    if start is None:
        start = Path.cwd()
    start = Path(start).resolve()

    current = start
    while True:
        if (current / "course-config.yaml").exists():
            return current
        if current.parent == current:
            return None
        current = current.parent


def load_config(course_root: Path = None) -> dict:
    """Load and validate course-config.yaml from the course root.

    If course_root is None, walks up from cwd to find the course root.
    Raises ConfigError if the config is missing or invalid.
    """
    if course_root is None:
        course_root = find_course_root()
        if course_root is None:
            raise ConfigError(
                "course-config.yaml not found. Are you inside a course repo?"
            )

    config_file = course_root / "course-config.yaml"
    if not config_file.exists():
        raise ConfigError(f"course-config.yaml not found in {course_root}")

    try:
        with config_file.open() as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"course-config.yaml does not parse: {e}")

    course = data.get("course")
    if not course:
        raise ConfigError("course-config.yaml is missing the top-level 'course:' key.")

    required_fields = ["name", "slug", "platform"]
    missing = [f for f in required_fields if not course.get(f)]
    if missing:
        raise ConfigError(
            f"course-config.yaml is missing required fields: {', '.join(missing)}"
        )

    # Knowledge-check rendering default for the whole course. Per-quiz mode
    # keys in each unit's knowledge-check.yaml override this. Default is
    # "study" (collapsible answers under each question, matching the
    # toolkit-wide default).
    kc_mode_raw = course.get("knowledge_check_mode")
    if kc_mode_raw is None:
        course["knowledge_check_mode"] = "study"
    else:
        if kc_mode_raw not in ("study", "test"):
            raise ConfigError(
                f"course-config.yaml: knowledge_check_mode must be 'study' "
                f"or 'test', got {kc_mode_raw!r}."
            )

    # Phase 18 visual polish fields. All optional. The static-web target
    # uses graceful defaults for courses that do not set them: a
    # gradient-only hero (no cover photo), no footer logo, the toolkit's
    # brand magenta as the only accent.
    cover_url = course.get("cover_image_url")
    if cover_url is not None and not isinstance(cover_url, str):
        raise ConfigError(
            "course-config.yaml: cover_image_url must be a string URL or path."
        )
    logo_url = course.get("logo_url")
    if logo_url is not None and not isinstance(logo_url, str):
        raise ConfigError(
            "course-config.yaml: logo_url must be a string URL or path."
        )
    secondary = course.get("brand_secondary_color")
    if secondary is not None:
        if not isinstance(secondary, str):
            raise ConfigError(
                "course-config.yaml: brand_secondary_color must be a CSS "
                "color string (e.g., '#00A3B5')."
            )
        # Loose hex check; CSS named colors and rgb() are also fine but
        # we just sanity-check shape so a typo like "magenta?" gets caught.
        s = secondary.strip()
        if s.startswith("#") and len(s) not in (4, 7, 9):
            raise ConfigError(
                f"course-config.yaml: brand_secondary_color hex form must "
                f"be #RGB, #RRGGBB, or #RRGGBBAA, got {secondary!r}."
            )

    # Platform-specific required fields and defaults.
    platform = course.get("platform")
    if platform == "canvas":
        has_account = course.get("canvas_account_id") is not None
        has_course = course.get("canvas_course_id") is not None
        if has_account and has_course:
            raise ConfigError(
                "course-config.yaml: platform 'canvas' has BOTH "
                "'canvas_account_id' and 'canvas_course_id' set. "
                "Pick one: canvas_account_id (create-new mode, requires "
                "admin rights to the account) OR canvas_course_id "
                "(update-existing mode, requires teacher rights on the "
                "specific course). Remove the field that does not apply."
            )
        if not has_account and not has_course:
            raise ConfigError(
                "course-config.yaml: platform 'canvas' requires either "
                "'canvas_account_id' OR 'canvas_course_id' under the "
                "'course:' block.\n"
                "  - canvas_account_id (integer): create-new mode. "
                "The toolkit creates a fresh course under the given "
                "account. Requires admin rights to that account.\n"
                "  - canvas_course_id (integer): update-existing mode. "
                "The toolkit pushes content into an existing Canvas "
                "course you already have teacher rights on. Find the "
                "ID in the URL when viewing the course on web: "
                "https://your-canvas.instructure.com/courses/NNNN."
            )

    if platform == "pdf":
        # PDF-specific fields with defaults. None of these are required;
        # they exist so the renderer always sees a value.
        course.setdefault("pdf_page_size", "letter")
        course.setdefault("pdf_microsim_strategy", "qr")
        course.setdefault("pdf_include_final", False)
        # pdf_microsim_base_url stays None if missing; the renderer emits
        # a placeholder for each MicroSim until it is set.
        valid_sizes = {"letter", "a4"}
        size = str(course.get("pdf_page_size") or "").lower()
        if size and size not in valid_sizes:
            raise ConfigError(
                f"course-config.yaml: pdf_page_size must be 'letter' or 'a4', "
                f"got '{course.get('pdf_page_size')}'"
            )
        valid_strategies = {"qr", "screenshot"}
        strat = str(course.get("pdf_microsim_strategy") or "").lower()
        if strat and strat not in valid_strategies:
            raise ConfigError(
                f"course-config.yaml: pdf_microsim_strategy must be 'qr' or "
                f"'screenshot', got '{course.get('pdf_microsim_strategy')}'"
            )

    course["_root"] = str(course_root)
    return course
