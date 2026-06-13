"""
DataLogger – records time-series experiment data to CSV or JSON files.

The DataLogger watches callable data sources and writes them to a file on
every call to :meth:`step`. Supports CSV and newline-delimited JSON (NDJSON)
formats, determined by the file extension.

Example::

    from bulletlab.logging import DataLogger

    logger = DataLogger()
    logger.watch("speed",  lambda: robot.speed)
    logger.watch("roll",   lambda: robot.roll)
    logger.watch("height", lambda: robot.base_position[2])
    logger.start("experiment_01.csv")

    for _ in range(1000):
        sim.step()
        logger.step()

    logger.stop()

Context manager usage::

    with DataLogger() as logger:
        logger.watch("speed", lambda: robot.speed)
        logger.start("run.csv")
        for _ in range(1000):
            sim.step()
            logger.step()
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from bulletlab.logging.csv_writer import CsvWriter
from bulletlab.logging.json_writer import JsonWriter


class DataLogger:
    """Records experiment data from callable sources to CSV or JSON files.

    Channels can be registered before or after calling :meth:`start`.
    The logger automatically determines the file format from the extension:
    ``.csv`` → CSV, ``.json`` or ``.ndjson`` → NDJSON.

    Args:
        include_timestamp: If ``True``, prepend a ``"t"`` column with the
            wall-clock time of each step. Defaults to ``True``.
        include_step: If ``True``, prepend a ``"step"`` column with the step
            index. Defaults to ``True``.

    Example::

        logger = DataLogger()
        logger.watch("speed", lambda: robot.speed)
        logger.start("run1.csv")
        for _ in range(1000):
            sim.step()
            logger.step()
        logger.stop()
    """

    def __init__(
        self,
        include_timestamp: bool = True,
        include_step: bool = True,
    ) -> None:
        self._channels: dict[str, Callable[[], Any]] = {}
        self._writer: CsvWriter | JsonWriter | None = None
        self._step_count: int = 0
        self._include_timestamp = include_timestamp
        self._include_step = include_step
        self._start_time: float = 0.0
        self._running: bool = False

    # ------------------------------------------------------------------
    # Channel registration
    # ------------------------------------------------------------------

    def watch(self, name: str, source: Callable[[], Any]) -> "DataLogger":
        """Register a data source to log.

        Args:
            name: Column name in the output file.
            source: Callable returning the current value.

        Returns:
            self, for method chaining.

        Example::

            logger.watch("speed", lambda: robot.speed)
            logger.watch("roll",  lambda: robot.roll)
        """
        self._channels[name] = source
        return self

    def unwatch(self, name: str) -> None:
        """Remove a previously registered channel.

        Args:
            name: Channel name to remove.
        """
        self._channels.pop(name, None)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self, filepath: str | Path) -> "DataLogger":
        """Open the output file and begin logging.

        Args:
            filepath: Path to the output file. Extension determines format:
                ``.csv`` for CSV, ``.json`` / ``.ndjson`` for NDJSON.

        Returns:
            self, for method chaining.

        Raises:
            RuntimeError: If the logger is already running.

        Example::

            logger.start("run1.csv")
        """
        if self._running:
            raise RuntimeError("DataLogger is already running. Call stop() first.")

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        ext = filepath.suffix.lower()

        fieldnames = self._build_fieldnames()

        if ext in (".json", ".ndjson", ".jsonl"):
            self._writer = JsonWriter(filepath)
        else:
            # Default to CSV
            self._writer = CsvWriter(filepath, fieldnames)

        self._step_count = 0
        self._start_time = time.monotonic()
        self._running = True
        return self

    def stop(self) -> None:
        """Flush and close the output file.

        Example::

            logger.stop()
        """
        if self._writer is not None:
            self._writer.close()
            self._writer = None
        self._running = False

    # ------------------------------------------------------------------
    # Data recording
    # ------------------------------------------------------------------

    def step(self, t: float | None = None) -> dict[str, Any]:
        """Record one row of data from all watched sources.

        Call this once per simulation step. If not started, this is a no-op.

        Args:
            t: Timestamp override. If ``None``, uses wall-clock elapsed time
                since :meth:`start` was called.

        Returns:
            The recorded row as a dictionary.

        Example::

            for _ in range(1000):
                sim.step()
                logger.step()
        """
        if not self._running or self._writer is None:
            return {}

        timestamp = t if t is not None else (time.monotonic() - self._start_time)
        row: dict[str, Any] = {}

        if self._include_step:
            row["step"] = self._step_count
        if self._include_timestamp:
            row["t"] = round(timestamp, 6)

        for name, source in self._channels.items():
            try:
                val = source()
            except Exception:
                val = float("nan")
            row[name] = val

        self._writer.write_row(row)
        self._step_count += 1
        return row

    def flush(self) -> None:
        """Manually flush buffered data to disk."""
        if self._writer is not None:
            self._writer.flush()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_fieldnames(self) -> list[str]:
        """Build the ordered list of field names including meta-columns."""
        fields: list[str] = []
        if self._include_step:
            fields.append("step")
        if self._include_timestamp:
            fields.append("t")
        fields.extend(self._channels.keys())
        return fields

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        """``True`` if the logger is currently recording."""
        return self._running

    @property
    def step_count(self) -> int:
        """Number of rows recorded since :meth:`start` was last called."""
        return self._step_count

    @property
    def channel_names(self) -> list[str]:
        """Names of all registered channels."""
        return list(self._channels.keys())

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "DataLogger":
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()

    def __repr__(self) -> str:
        status = "running" if self._running else "stopped"
        return f"DataLogger({status}, channels={list(self._channels.keys())}, steps={self._step_count})"
