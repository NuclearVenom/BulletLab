"""
LivePlot – real-time data visualization using PyQtGraph.

LivePlot opens a PyQtGraph window and plots live data from callable sources.
Multiple traces can be added with custom colors. The plot supports zoom,
pan (via PyQtGraph's native interaction), pause, resume, and image export.

Example::

    from bulletlab.plotting import LivePlot

    plot = LivePlot(title="Robot Telemetry", max_points=500)
    plot.watch("Speed",  lambda: robot.speed, color="#00ff88")
    plot.watch("Roll",   lambda: robot.roll,  color="#ff4488")
    plot.watch("Height", lambda: robot.base_position[2], color="#44aaff")
    plot.start()

    for _ in range(5000):
        sim.step()
        plot.update()

    plot.stop()

Non-blocking usage::

    plot.start()      # opens window in Qt thread
    # ... simulation loop calls plot.update() each step
    plot.stop()       # closes window
"""

from __future__ import annotations

import sys
import time
from collections import deque
from typing import Any, Callable, Optional

# PyQtGraph and Qt are optional — graceful fallback if not installed
try:
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtWidgets, QtCore

    _HAS_PYQTGRAPH = True
except ImportError:  # pragma: no cover
    _HAS_PYQTGRAPH = False
    pg = None  # type: ignore[assignment]
    QtWidgets = None  # type: ignore[assignment]
    QtCore = None  # type: ignore[assignment]


class _PlotSeries:
    """Internal container for one data series."""

    def __init__(
        self,
        name: str,
        source: Callable[[], Any],
        color: str,
        max_points: int,
    ) -> None:
        self.name = name
        self.source = source
        self.color = color
        self.max_points = max_points
        self.timestamps: deque[float] = deque(maxlen=max_points)
        self.values: deque[float] = deque(maxlen=max_points)
        self.curve: Any = None  # pyqtgraph PlotDataItem


class LivePlot:
    """Real-time multi-trace plotting window powered by PyQtGraph.

    Opens a separate Qt window. The simulation loop must call
    :meth:`update` periodically to push new data and refresh the display.

    Args:
        title: Window title.
        max_points: Maximum number of data points per trace (older points
            are dropped in a rolling fashion).
        update_interval_ms: Minimum time between display refreshes in
            milliseconds. Reduces overhead when :meth:`update` is called
            faster than needed.
        y_label: Y-axis label.
        x_label: X-axis label.

    Example::

        plot = LivePlot(title="Speed vs Time", max_points=300)
        plot.watch("Speed", lambda: robot.speed, color="#00ff88")
        plot.start()
        for _ in range(1000):
            sim.step()
            plot.update()
        plot.stop()
    """

    def __init__(
        self,
        title: str = "BulletLab Live Plot",
        max_points: int = 500,
        update_interval_ms: int = 33,
        y_label: str = "Value",
        x_label: str = "Time (s)",
    ) -> None:
        self._title = title
        self._max_points = max_points
        self._update_interval = update_interval_ms / 1000.0
        self._y_label = y_label
        self._x_label = x_label

        self._series: list[_PlotSeries] = []
        self._running = False
        self._paused = False
        self._start_time: float = 0.0
        self._last_refresh: float = 0.0

        # Qt objects (None until start() is called)
        self._app: Any = None
        self._window: Any = None
        self._plot_widget: Any = None

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def watch(
        self,
        name: str,
        source: Callable[[], Any],
        color: str = "#ffffff",
    ) -> "LivePlot":
        """Add a data series to the plot.

        Args:
            name: Series name (shown in legend).
            source: Callable returning the current value.
            color: Line color as a hex string (e.g. ``"#00ff88"``).

        Returns:
            self, for method chaining.

        Example::

            plot.watch("Speed", lambda: robot.speed, color="#00ff88")
        """
        series = _PlotSeries(
            name=name,
            source=source,
            color=color,
            max_points=self._max_points,
        )
        self._series.append(series)
        return self

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> "LivePlot":
        """Open the plot window.

        Creates a Qt application if one does not already exist.
        Non-blocking: the window is opened and control returns immediately.
        Call :meth:`update` in your simulation loop to refresh the plot.

        Returns:
            self, for method chaining.

        Raises:
            ImportError: If PyQtGraph is not installed.

        Example::

            plot.start()
        """
        if not _HAS_PYQTGRAPH:
            print(
                "[BulletLab] LivePlot: PyQtGraph is not installed. "
                "Install with: pip install pyqtgraph PyQt5"
            )
            return self

        if self._running:
            return self

        # Ensure Qt application exists
        self._app = QtWidgets.QApplication.instance()
        if self._app is None:
            self._app = QtWidgets.QApplication(sys.argv)

        # Create window
        self._window = pg.GraphicsLayoutWidget(title=self._title, show=True)
        self._window.setWindowTitle(self._title)
        self._window.resize(900, 500)

        self._plot_widget = self._window.addPlot(
            title=self._title,
            labels={"left": self._y_label, "bottom": self._x_label},
        )
        self._plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self._plot_widget.addLegend()

        # Create curves for each series
        for series in self._series:
            series.curve = self._plot_widget.plot(
                pen=pg.mkPen(color=series.color, width=2),
                name=series.name,
            )

        self._start_time = time.monotonic()
        self._last_refresh = self._start_time
        self._running = True
        return self

    def stop(self) -> None:
        """Close the plot window and release resources.

        Example::

            plot.stop()
        """
        self._running = False
        if self._window is not None and _HAS_PYQTGRAPH:
            try:
                self._window.close()
            except Exception:
                pass
            self._window = None

    # ------------------------------------------------------------------
    # Update loop
    # ------------------------------------------------------------------

    def update(self, t: float | None = None) -> None:
        """Sample all data sources and refresh the plot display.

        Call this once per simulation step. Refresh rate is throttled by
        ``update_interval_ms`` to avoid excessive Qt overhead.

        Args:
            t: Timestamp override. If ``None``, uses wall-clock elapsed time
                since :meth:`start` was called.

        Example::

            for _ in range(5000):
                sim.step()
                plot.update()
        """
        if not self._running or self._paused:
            return

        timestamp = t if t is not None else (time.monotonic() - self._start_time)

        # Sample all series
        for series in self._series:
            try:
                val = float(series.source())
            except Exception:
                val = float("nan")
            series.timestamps.append(timestamp)
            series.values.append(val)

        # Throttle display updates
        now = time.monotonic()
        if now - self._last_refresh < self._update_interval:
            return

        self._last_refresh = now
        self._refresh_display()

    def _refresh_display(self) -> None:
        """Update the Qt plot curves from buffered data."""
        if not _HAS_PYQTGRAPH or self._plot_widget is None:
            return

        import numpy as np

        for series in self._series:
            if series.curve is not None and len(series.timestamps) > 0:
                x = np.array(list(series.timestamps))
                y = np.array(list(series.values))
                series.curve.setData(x=x, y=y)

        # Process Qt events
        try:
            self._app.processEvents()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    def pause(self) -> None:
        """Pause data sampling and display updates.

        Example::

            plot.pause()
        """
        self._paused = True

    def resume(self) -> None:
        """Resume a paused plot.

        Example::

            plot.resume()
        """
        self._paused = False

    def clear(self) -> None:
        """Clear all data buffers (but keep series registrations).

        Example::

            plot.clear()
        """
        for series in self._series:
            series.timestamps.clear()
            series.values.clear()

    def export(self, filepath: str) -> None:
        """Export the current plot as an image.

        Args:
            filepath: Output file path. Supported formats: PNG, JPG (via Qt).

        Example::

            plot.export("speed_plot.png")
        """
        if not _HAS_PYQTGRAPH or self._window is None:
            print("[BulletLab] LivePlot: Cannot export — plot window not open.")
            return
        try:
            exporter = pg.exporters.ImageExporter(self._plot_widget)
            exporter.export(filepath)
        except Exception as exc:
            print(f"[BulletLab] LivePlot export failed: {exc}")

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        """``True`` if the plot window is open."""
        return self._running

    @property
    def is_paused(self) -> bool:
        """``True`` if sampling is paused."""
        return self._paused

    @property
    def series_names(self) -> list[str]:
        """Names of all registered data series."""
        return [s.name for s in self._series]

    def __repr__(self) -> str:
        status = "running" if self._running else "stopped"
        return f"LivePlot({self._title!r}, {status}, series={self.series_names})"
