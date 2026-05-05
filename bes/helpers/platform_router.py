"""Platform router.

Reads the platform field from course-config.yaml and dispatches to the
correct sync implementation. thinkific (Phase 2) and canvas (Phase 11) are
wired up; the others raise PlatformError until their phase ships.
"""


class PlatformError(Exception):
    """Raised when the platform is unknown or not yet implemented."""


SUPPORTED_PLATFORMS = {
    "thinkific": "implemented",
    "canvas": "implemented",
    "google-classroom": "deferred",
    "static-web": "deferred",
    "pdf": "deferred",
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
            f"For now, 'thinkific' and 'canvas' are the supported sync targets."
        )

    if platform == "thinkific":
        from sync.thinkific.lib import sync
        return sync

    if platform == "canvas":
        from sync.canvas.lib import sync
        return sync

    raise PlatformError(f"Internal error: no sync function for '{platform}'.")
