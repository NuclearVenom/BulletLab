"""
Session-scoped temporary cache for BulletLab Arsenal.

Arsenal robot assets downloaded for ``Robot.load("arsenal:...")`` are stored
here for the duration of the Python process.  The directory is created on
first access and automatically deleted on process exit via ``atexit``.

Users should never need to interact with this module directly.
"""

from __future__ import annotations

import atexit
import shutil
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_session_cache: Path | None = None


def get_session_cache() -> Path:
    """Return the path to the Arsenal session cache directory.

    The directory is created lazily on first call and registered for
    automatic cleanup when the Python process exits.

    Returns:
        :class:`pathlib.Path` to the temporary cache directory.

    Example::

        cache = get_session_cache()
        dest = cache / "reference_bot"
        dest.mkdir(parents=True, exist_ok=True)
    """
    global _session_cache
    if _session_cache is None:
        _session_cache = Path(tempfile.mkdtemp(prefix="bulletlab_arsenal_"))
        atexit.register(_cleanup_cache)
    return _session_cache


def _cleanup_cache() -> None:
    """Remove the session cache directory on process exit.

    Silently ignores errors so that a missing or partially-written cache
    does not crash the process during shutdown.
    """
    global _session_cache
    if _session_cache is not None and _session_cache.exists():
        shutil.rmtree(_session_cache, ignore_errors=True)
        _session_cache = None
