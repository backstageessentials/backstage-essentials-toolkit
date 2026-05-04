"""Platform router.

Reads the platform field from course-config.yaml and dispatches to the
correct sync implementation. Right now only thinkific is wired up; the
others raise NotImplementedError until Phase 4.
"""


class PlatformError(Exception):
    """Raised when the platform is unknown or not yet implemented."""


SUPPORTED_PLATFORMS = {
    "thinkific": "implemented",
    "canvas": "phase4",
    "google-classroom": "phase4",
    "static-web": "phase4",
    "pdf": "phase4",
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
    if status == "phase4":
        raise PlatformError(
            f"Platform '{platform}' is not yet implemented. "
            f"Coming in Phase 4 of the toolkit. For now, only 'thinkific' works."
        )

    if platform == "thinkific":
        from sync.thinkific.lib import sync
        return sync

    raise PlatformError(f"Internal error: no sync function for '{platform}'.")
