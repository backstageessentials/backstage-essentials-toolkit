"""Static-web sync library: HTML preview generation with Mermaid support."""

from .preview import (
    render_unit_preview,
    render_all_units,
    render_course_preview,
    write_course_preview,
    render_final_preview,
    write_final_preview,
    render_test_section,
    detect_quiz_mode,
    BRAND_COLORS,
)

__all__ = [
    "render_unit_preview",
    "render_all_units",
    "render_course_preview",
    "write_course_preview",
    "render_final_preview",
    "write_final_preview",
    "render_test_section",
    "detect_quiz_mode",
    "BRAND_COLORS",
]
