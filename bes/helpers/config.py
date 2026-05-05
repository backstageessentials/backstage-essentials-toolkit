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

    # Platform-specific required fields and defaults.
    platform = course.get("platform")
    if platform == "canvas":
        if not course.get("canvas_account_id"):
            raise ConfigError(
                "course-config.yaml: platform 'canvas' requires a "
                "'canvas_account_id' field under the 'course:' block. "
                "On hosted Canvas the root account is usually 1; on an "
                "institutional instance, ask your Canvas admin for the "
                "sub-account ID you have rights to use."
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
