"""
PlotsPanel – renders inline live plots using ImGui's plot_lines primitive.

Displays sparkline-style charts for telemetry channel histories directly
inside the BulletLab ImGui control window. These are lightweight inline
plots (not PyQtGraph). For full-featured windowed plots, use LivePlot.

Example::

    from bulletlab.ui.panels.plots import PlotsPanel
    from bulletlab.telemetry import TelemetryManager

    telemetry = TelemetryManager()
    telemetry.watch("Speed", lambda: robot.speed)

    plots = PlotsPanel(telemetry)
    plots.render()
"""

from __future__ import annotations

import array
from typing import TYPE_CHECKING

try:
    import imgui

    _HAS_IMGUI = True
except ImportError:  # pragma: no cover
    imgui = None  # type: ignore[assignment]
    _HAS_IMGUI = False

if TYPE_CHECKING:
    from bulletlab.telemetry.manager import TelemetryManager


class PlotsPanel:
    """Renders inline sparkline plots for all telemetry channels.

    Uses ImGui's built-in ``plot_lines`` which requires no external
    plotting library. For production-quality plots, use
    :class:`~bulletlab.plotting.live_plot.LivePlot`.

    Args:
        telemetry: The :class:`~bulletlab.telemetry.manager.TelemetryManager`
            providing channel histories.
        plot_height: Height of each individual sparkline in pixels.
        max_display: Maximum number of channels to plot simultaneously.

    Example::

        plots_panel = PlotsPanel(telemetry)
        plots_panel.render()
    """

    def __init__(
        self,
        telemetry: "TelemetryManager",
        plot_height: float = 60.0,
        max_display: int = 8,
    ) -> None:
        self._telemetry = telemetry
        self._plot_height = plot_height
        self._max_display = max_display

    def render(self) -> None:
        """Draw the plots panel contents.

        Must be called inside an active ImGui window context.
        """
        if not _HAS_IMGUI:
            return

        channels = self._telemetry.channels
        if not channels:
            imgui.text_colored("No channels to plot.", 0.5, 0.5, 0.5, 1.0)
            imgui.text("Add channels with telemetry.watch(...)")
            return

        shown = 0
        for name, channel in channels.items():
            if shown >= self._max_display:
                imgui.text_colored(
                    f"... and {len(channels) - shown} more channels",
                    0.5, 0.5, 0.5, 1.0,
                )
                break

            values = channel.values
            if not values:
                imgui.text(f"{name}: (no data)")
                shown += 1
                continue

            # Build a contiguous C-float buffer.
            # imgui.plot_lines() requires a bytes-like / buffer object —
            # a plain Python list raises TypeError.
            float_vals: list[float] = []
            for v in values:
                try:
                    float_vals.append(float(v))
                except (TypeError, ValueError):
                    float_vals.append(0.0)

            if not float_vals:
                shown += 1
                continue

            buf = array.array("f", float_vals)   # contiguous single-precision floats

            latest = float_vals[-1]
            unit = channel.unit
            unit_str = f" {unit}" if unit else ""
            vmin = min(float_vals)
            vmax = max(float_vals)
            overlay = f"{latest:.3f}{unit_str}"
            avail_w = imgui.get_content_region_available()[0]

            try:
                imgui.plot_lines(
                    f"##{name}_plot",
                    buf,
                    overlay_text=overlay,
                    scale_min=vmin - abs(vmin) * 0.1 - 1e-6,
                    scale_max=vmax + abs(vmax) * 0.1 + 1e-6,
                    graph_size=(avail_w, self._plot_height),
                )
            except Exception:
                # Graceful fallback if this imgui version's plot_lines binding
                # uses a different signature
                imgui.text(f"{name}: {latest:.4f}{unit_str}")
                shown += 1
                continue

            imgui.text_colored(
                f"{name}: {latest:.4f}{unit_str}  [{vmin:.3f} – {vmax:.3f}]",
                0.7, 0.9, 0.7, 1.0,
            )
            imgui.separator()
            shown += 1

    def __repr__(self) -> str:
        return f"PlotsPanel(channels={self._telemetry.channel_names})"
