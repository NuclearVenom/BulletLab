"""
JSON/NDJSON writer backend for DataLogger.

Internal module — used by :class:`~bulletlab.logging.logger.DataLogger`.
Writes newline-delimited JSON (one JSON object per line) for streaming-friendly
log files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonWriter:
    """Writes log data as newline-delimited JSON (NDJSON format).

    Each call to :meth:`write_row` appends a single JSON object to the file.

    Args:
        filepath: Output file path.

    Example::

        writer = JsonWriter("run1.json")
        writer.write_row({"t": 0.0, "speed": 1.5, "roll": 0.01})
        writer.close()
    """

    def __init__(self, filepath: str | Path) -> None:
        self._filepath = Path(filepath)
        self._file = open(self._filepath, "w", encoding="utf-8")

    def write_row(self, row: dict[str, Any]) -> None:
        """Write a single record as a JSON line.

        Args:
            row: Dictionary of field names to values.
        """
        self._file.write(json.dumps(row, default=_json_default) + "\n")

    def flush(self) -> None:
        """Flush the write buffer to disk."""
        self._file.flush()

    def close(self) -> None:
        """Close the file handle."""
        if not self._file.closed:
            self._file.flush()
            self._file.close()

    def __del__(self) -> None:
        self.close()


def _json_default(obj: Any) -> Any:
    """Fallback JSON serializer for numpy types and similar."""
    try:
        import numpy as np  # noqa: PLC0415

        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
    except ImportError:
        pass
    return str(obj)
