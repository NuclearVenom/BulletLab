"""
CSV writer backend for DataLogger.

Internal module — used by :class:`~bulletlab.logging.logger.DataLogger`.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


class CsvWriter:
    """Writes tabular log data to a CSV file.

    Args:
        filepath: Output file path.
        fieldnames: Column names.

    Example::

        writer = CsvWriter("run1.csv", ["t", "speed", "roll"])
        writer.write_row({"t": 0.0, "speed": 1.5, "roll": 0.01})
        writer.close()
    """

    def __init__(self, filepath: str | Path, fieldnames: list[str]) -> None:
        self._filepath = Path(filepath)
        self._fieldnames = fieldnames
        self._file = open(self._filepath, "w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=self._fieldnames)
        self._writer.writeheader()

    def write_row(self, row: dict[str, Any]) -> None:
        """Write a single row to the CSV file.

        Args:
            row: Dictionary mapping column names to values.
        """
        self._writer.writerow(row)

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
