"""Canvas sync library.

The main entry point is `sync()` in sync.py. Both `bes sync` and the course's
local `scripts/sync.py` shim end up calling it.
"""

from .sync import sync

__all__ = ["sync"]
