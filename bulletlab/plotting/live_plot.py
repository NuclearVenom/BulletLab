"""
LivePlot – real-time data visualization using ImPlot (imgui-bundle).

LivePlot opens a standalone GLFW window and plots live data from callable sources.
Multiple traces can be added with custom colors. The plot supports zoom,
pan, pause, and resume natively via ImPlot.

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

    plot.start()      # opens window via GLFW
    # ... simulation loop calls plot.update() each step
    plot.stop()       # closes window
"""

from __future__ import annotations

import sys
import time
from collections import deque
from typing import Any, Callable
import OpenGL.GL as gl

try:
    from imgui_bundle import imgui, implot
    
    try:
        import imgui_bundle.glfw as glfw
    except ImportError:
        import glfw  # type: ignore
        
    try:
        from imgui_bundle.python_backends.glfw_backend import GlfwRenderer
    except ImportError:
        from imgui_bundle.python_backends.opengl_backend import OpenGLRenderer as GlfwRenderer  # type: ignore

    import numpy as np
    _HAS_IMPLOT = True
except ImportError:
    _HAS_IMPLOT = False

def hex_to_vec4(hex_str: str) -> imgui.ImVec4:
    """Convert #RRGGBB to ImVec4."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 6:
        r, g, b = (int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        return imgui.ImVec4(r, g, b, 1.0)
    return imgui.ImVec4(1.0, 1.0, 1.0, 1.0)


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


class LivePlot:
    """Real-time multi-trace plotting window powered by ImPlot.

    Opens a separate GLFW window. The simulation loop must call
    :meth:`update` periodically to push new data and refresh the display.
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

        # ImGui / GLFW objects
        self._window: Any = None
        self._impl: Any = None
        self._imgui_context: Any = None
        self._implot_context: Any = None

    def watch(
        self,
        name: str,
        source: Callable[[], Any],
        color: str = "#ffffff",
    ) -> "LivePlot":
        series = _PlotSeries(
            name=name,
            source=source,
            color=color,
            max_points=self._max_points,
        )
        self._series.append(series)
        return self

    def start(self) -> "LivePlot":
        if not _HAS_IMPLOT:
            print(
                "[BulletLab] LivePlot: imgui-bundle with implot is not available. "
                "Install with: pip install imgui-bundle glfw numpy"
            )
            return self

        if self._running:
            return self

        if not glfw.init():
            raise RuntimeError("GLFW could not be initialized")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, 1)

        self._window = glfw.create_window(900, 500, self._title, None, None)
        if not self._window:
            glfw.terminate()
            raise RuntimeError("Could not create GLFW window")
            
        glfw.make_context_current(self._window)
        glfw.swap_interval(1)

        self._imgui_context = imgui.create_context()
        imgui.set_current_context(self._imgui_context)
        
        self._implot_context = implot.create_context()
        implot.set_current_context(self._implot_context)

        imgui.style_colors_dark()
        
        self._impl = GlfwRenderer(self._window)

        self._start_time = time.monotonic()
        self._last_refresh = self._start_time
        self._running = True
        return self

    def stop(self) -> None:
        self._running = False
        if self._impl is not None:
            self._impl.shutdown()
        if self._implot_context is not None:
            implot.destroy_context(self._implot_context)
        if self._imgui_context is not None:
            imgui.destroy_context(self._imgui_context)
        if self._window is not None:
            glfw.destroy_window(self._window)
        
        self._window = None
        self._impl = None
        self._imgui_context = None
        self._implot_context = None

    def update(self, t: float | None = None) -> None:
        if not self._running:
            return
            
        if glfw.window_should_close(self._window):
            self.stop()
            return

        if not self._paused:
            timestamp = t if t is not None else (time.monotonic() - self._start_time)

            for series in self._series:
                try:
                    val = float(series.source())
                except Exception:
                    val = float("nan")
                series.timestamps.append(timestamp)
                series.values.append(val)

        now = time.monotonic()
        if now - self._last_refresh < self._update_interval:
            return

        self._last_refresh = now
        self._refresh_display()

    def _refresh_display(self) -> None:
        if not _HAS_IMPLOT or self._window is None:
            return

        glfw.poll_events()
        self._impl.process_inputs()
        
        imgui.set_current_context(self._imgui_context)
        implot.set_current_context(self._implot_context)
        imgui.new_frame()
        
        # Render full screen window
        viewport = imgui.get_main_viewport()
        imgui.set_next_window_pos(viewport.pos)
        imgui.set_next_window_size(viewport.size)
        
        flags = (imgui.WindowFlags_.no_title_bar.value | 
                 imgui.WindowFlags_.no_resize.value | 
                 imgui.WindowFlags_.no_move.value | 
                 imgui.WindowFlags_.no_collapse.value |
                 imgui.WindowFlags_.no_bring_to_display_front.value)
                 
        imgui.begin(self._title, True, flags)
        
        avail = imgui.get_content_region_available()
        
        if implot.begin_plot(self._title, avail):
            implot.setup_axes(self._x_label, self._y_label)
            
            for series in self._series:
                if len(series.timestamps) > 0:
                    x = np.array(list(series.timestamps), dtype=np.float64)
                    y = np.array(list(series.values), dtype=np.float64)
                    
                    implot.set_next_line_style(hex_to_vec4(series.color), 2.0)
                    implot.plot_line(series.name, x, y)
                    
            implot.end_plot()
            
        imgui.end()
        
        gl.glClearColor(0.1, 0.1, 0.1, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        imgui.render()
        self._impl.render(imgui.get_draw_data())
        glfw.swap_buffers(self._window)

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def clear(self) -> None:
        for series in self._series:
            series.timestamps.clear()
            series.values.clear()

    def export(self, filepath: str) -> None:
        print("[BulletLab] LivePlot: image export is not natively supported in ImPlot yet. Please use ImPlot's right-click menu to take a screenshot.")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def series_names(self) -> list[str]:
        return [s.name for s in self._series]

    def __repr__(self) -> str:
        status = "running" if self._running else "stopped"
        return f"LivePlot({self._title!r}, {status}, series={self.series_names})"
