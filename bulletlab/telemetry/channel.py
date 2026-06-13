"""
TelemetryChannel – a single monitored data channel.

A channel wraps a callable (lambda, method, or property function) and
accumulates a rolling history of (timestamp, value) pairs.

Example::

    channel = TelemetryChannel("Speed", lambda: robot.speed)
    channel.poll(t=0.1)
    print(channel.latest)    # most recent value
    print(channel.history)   # deque of (t, value)
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any, Callable, Optional


class TelemetryChannel:
    """A single named data stream with a rolling history buffer.

    Args:
        name: Human-readable channel name.
        source: Callable that returns the current value when called.
        history_len: Maximum number of samples to retain in history.
            Defaults to 1000.
        unit: Optional unit string (e.g. ``"m/s"``, ``"rad"``).

    Example::

        ch = TelemetryChannel("Roll", lambda: robot.roll, unit="rad")
        ch.poll(0.0)
        print(ch.latest)
        print(ch.history[-1])   # (timestamp, value)
    """

    def __init__(
        self,
        name: str,
        source: Callable[[], Any],
        history_len: int = 1000,
        unit: str = "",
    ) -> None:
        self._name = name
        self._source = source
        self._history: deque[tuple[float, Any]] = deque(maxlen=history_len)
        self._unit = unit
        self._latest: Any = None
        self._last_poll_time: float = 0.0

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    def poll(self, t: float | None = None) -> Any:
        """Sample the source and store the result in history.

        Args:
            t: Timestamp for this sample. If ``None``, uses
                :func:`time.monotonic`.

        Returns:
            The sampled value.

        Example::

            value = channel.poll(t=sim.elapsed_time)
        """
        timestamp = t if t is not None else time.monotonic()
        try:
            value = self._source()
        except Exception as exc:
            value = float("nan")

        self._latest = value
        self._last_poll_time = timestamp
        self._history.append((timestamp, value))
        return value

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Channel name."""
        return self._name

    @property
    def unit(self) -> str:
        """Measurement unit string (e.g. ``"m/s"``)."""
        return self._unit

    @property
    def latest(self) -> Any:
        """Most recently polled value, or ``None`` if never polled."""
        return self._latest

    @property
    def history(self) -> deque[tuple[float, Any]]:
        """Rolling history as a deque of ``(timestamp, value)`` pairs."""
        return self._history

    @property
    def timestamps(self) -> list[float]:
        """List of all stored timestamps."""
        return [t for t, _ in self._history]

    @property
    def values(self) -> list[Any]:
        """List of all stored values."""
        return [v for _, v in self._history]

    def clear(self) -> None:
        """Clear the history buffer."""
        self._history.clear()
        self._latest = None

    def __repr__(self) -> str:
        unit_str = f" {self._unit}" if self._unit else ""
        return f"TelemetryChannel({self._name!r}, latest={self._latest}{unit_str})"
