"""
TelemetryManager – watches and aggregates multiple data channels.

The TelemetryManager polls all registered channels on each call to
:meth:`update` and provides a unified snapshot of the current state.

Example::

    from bulletlab.telemetry import TelemetryManager

    telemetry = TelemetryManager()
    telemetry.watch("Speed",  lambda: robot.base_velocity[0], unit="m/s")
    telemetry.watch("Roll",   lambda: robot.roll, unit="rad")
    telemetry.watch("Height", lambda: robot.base_position[2], unit="m")

    for _ in range(1000):
        sim.step()
        telemetry.update(t=sim.elapsed_time)

    print(telemetry.snapshot())
    print(telemetry.get("Speed"))
"""

from __future__ import annotations

import time
from typing import Any, Callable

from bulletlab.telemetry.channel import TelemetryChannel


class TelemetryManager:
    """Aggregates multiple :class:`~bulletlab.telemetry.channel.TelemetryChannel` instances.

    Register channels with :meth:`watch`, then call :meth:`update` every
    simulation step. Retrieve the latest values via :meth:`get` or
    :meth:`snapshot`.

    Args:
        history_len: Default history buffer length for new channels.

    Example::

        telemetry = TelemetryManager()
        telemetry.watch("Roll", lambda: robot.roll, unit="rad")
        telemetry.watch("Speed", lambda: robot.speed, unit="m/s")

        for _ in range(1000):
            sim.step()
            telemetry.update(t=sim.elapsed_time)

        print(telemetry.snapshot())
    """

    def __init__(self, history_len: int = 1000) -> None:
        self._channels: dict[str, TelemetryChannel] = {}
        self._history_len = history_len
        self._last_update_time: float = 0.0

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def watch(
        self,
        name: str,
        source: Callable[[], Any],
        unit: str = "",
        history_len: int | None = None,
    ) -> TelemetryChannel:
        """Register a new channel to monitor.

        Args:
            name: Human-readable channel name.
            source: A callable (lambda, function, or method) that returns
                the current value when called.
            unit: Optional unit string (e.g. ``"m/s"``).
            history_len: History buffer size. Defaults to manager's default.

        Returns:
            The created :class:`~bulletlab.telemetry.channel.TelemetryChannel`.

        Example::

            telemetry.watch("Speed", lambda: robot.speed, unit="m/s")
            telemetry.watch("Joint_1", robot.joints["iiwa_joint_1"].position)
        """
        if callable(source):
            source_fn = source
        else:
            # Allow passing a property value directly as a lambda
            _val = source
            source_fn = lambda: _val  # noqa: E731

        hlen = history_len if history_len is not None else self._history_len
        channel = TelemetryChannel(name=name, source=source_fn, history_len=hlen, unit=unit)
        self._channels[name] = channel
        return channel

    def unwatch(self, name: str) -> None:
        """Remove a channel by name.

        Args:
            name: Channel name to remove.
        """
        self._channels.pop(name, None)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, t: float | None = None) -> dict[str, Any]:
        """Poll all channels and return a snapshot of current values.

        Args:
            t: Timestamp for this update cycle. If ``None``, uses
                :func:`time.monotonic`.

        Returns:
            Dictionary mapping channel names to their current values.

        Example::

            values = telemetry.update(t=sim.elapsed_time)
        """
        timestamp = t if t is not None else time.monotonic()
        self._last_update_time = timestamp
        result = {}
        for name, channel in self._channels.items():
            result[name] = channel.poll(t=timestamp)
        return result

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get(self, name: str, default: Any = None) -> Any:
        """Return the latest value for a channel.

        Args:
            name: Channel name.
            default: Value to return if channel does not exist.

        Example::

            speed = telemetry.get("Speed")
        """
        channel = self._channels.get(name)
        return channel.latest if channel is not None else default

    def snapshot(self) -> dict[str, Any]:
        """Return a dictionary of all channel names to their latest values.

        Example::

            data = telemetry.snapshot()
            print(data["Speed"])
        """
        return {name: ch.latest for name, ch in self._channels.items()}

    def history(self, name: str) -> list[tuple[float, Any]]:
        """Return the full history for a channel.

        Args:
            name: Channel name.

        Returns:
            List of ``(timestamp, value)`` tuples.

        Example::

            times_and_vals = telemetry.history("Speed")
        """
        channel = self._channels.get(name)
        if channel is None:
            return []
        return list(channel.history)

    def values_array(self, name: str) -> list[Any]:
        """Return only the values (no timestamps) for a channel.

        Args:
            name: Channel name.

        Returns:
            List of values in chronological order.
        """
        channel = self._channels.get(name)
        if channel is None:
            return []
        return channel.values

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def clear_history(self) -> None:
        """Clear history buffers for all channels."""
        for channel in self._channels.values():
            channel.clear()

    def clear_all(self) -> None:
        """Remove all registered channels."""
        self._channels.clear()

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def channels(self) -> dict[str, TelemetryChannel]:
        """Dictionary of all registered channels."""
        return dict(self._channels)

    @property
    def channel_names(self) -> list[str]:
        """List of all registered channel names."""
        return list(self._channels.keys())

    def __len__(self) -> int:
        return len(self._channels)

    def __contains__(self, name: str) -> bool:
        return name in self._channels

    def __repr__(self) -> str:
        return f"TelemetryManager(channels={list(self._channels.keys())})"
