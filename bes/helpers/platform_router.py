"""Platform router.

Reads the platform field from course-config.yaml and dispatches to the
correct sync implementation. thinkific (Phase 2), canvas (Phase 11), pdf
(Phase 12), and talentlms (Phase 16) are wired up; the others raise
PlatformError until their phase ships.

The sync skill packages live as siblings of the bes package at the toolkit
root (e.g., `<toolkit-root>/sync/canvas/lib/sync.py`). The editable install
only registers `bes` as a top-level package, so we add the toolkit root to
sys.path on demand before importing a sync skill.
"""

import sys
from pathlib import Path


_TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent


def _ensure_toolkit_on_path() -> None:
    """Make `sync.<platform>.lib` importable regardless of cwd."""
    root = str(_TOOLKIT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


class PlatformError(Exception):
    """Raised when the platform is unknown or not yet implemented."""


SUPPORTED_PLATFORMS = {
    "thinkific": "implemented",
    "canvas": "implemented",
    "pdf": "implemented",
    "talentlms": "implemented",
    "google-classroom": "deferred",
    "static-web": "deferred",
}


def get_sync_function(platform: str):
    """Return the sync() function for the given platform.

    Raises PlatformError if the platform is unknown or not yet implemented.
    """
    if platform not in SUPPORTED_PLATFORMS:
        raise PlatformError(
            f"Unknown platform '{platform}'. Valid: {', '.join(SUPPORTED_PLATFORMS)}"
        )

    status = SUPPORTED_PLATFORMS[platform]
    if status == "deferred":
        raise PlatformError(
            f"Platform '{platform}' is not yet implemented. "
            f"For now, 'thinkific', 'canvas', 'talentlms', and 'pdf' are the "
            f"supported sync targets."
        )

    _ensure_toolkit_on_path()

    if platform == "thinkific":
        from sync.thinkific.lib import sync
        return sync

    if platform == "canvas":
        from sync.canvas.lib import sync
        return sync

    if platform == "pdf":
        from sync.pdf.lib import sync
        return sync

    if platform == "talentlms":
        from sync.talentlms.lib import sync
        return sync

    raise PlatformError(f"Internal error: no sync function for '{platform}'.")


def get_export_pdf_function():
    """Return the export_pdf() function from sync/pdf/.

    Used by `bes export-pdf` to produce a PDF regardless of the course's
    primary platform. Imports the same module the pdf platform sync uses,
    so the renderer code is shared between bes sync (when platform: pdf)
    and bes export-pdf (always available).
    """
    _ensure_toolkit_on_path()
    from sync.pdf.lib import export_pdf
    return export_pdf
