"""Static-web sync library: HTML preview generation with Mermaid support."""

from .preview import (
    render_unit_preview,
    render_all_units,
    render_course_preview,
    write_course_preview,
    BRAND_COLORS,
)

__all__ = [
    "render_unit_preview",
    "render_all_units",
    "render_course_preview",
    "write_course_preview",
    "BRAND_COLORS",
]
