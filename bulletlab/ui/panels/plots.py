"""
PlotsPanel – renders inline live plots using ImGui's plot_lines primitive.

Displays sparkline-style charts for telemetry channel histories directly
inside the BulletLab ImGui control window. These are lightweight inline
plots. For full-featured windowed ImPlot graphs, use LivePlot.

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
    from imgui_bundle import imgui, implot
    _HAS_IMGUI = True
    _HAS_IMPLOT = True
except ImportError:
    imgui = None  # type: ignore[assignment]
    implot = None
    _HAS_IMGUI = False
    _HAS_IMPLOT = False

if TYPE_CHECKING:
    from bulletlab.telemetry.manager import TelemetryManager


class PlotsPanel:
    """Renders inline plots for all telemetry channels using ImPlot.

    Args:
        telemetry: The :class:`~bulletlab.telemetry.manager.TelemetryManager`
            providing channel histories.
        plot_height: Height of each individual plot in pixels.
        max_display: Maximum number of channels to plot simultaneously.

    Example::

        plots_panel = PlotsPanel(telemetry)
        plots_panel.render()
    """

    def __init__(
        self,
        telemetry: "TelemetryManager",
        plot_height: float = 120.0,  # Increased height for ImPlot
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
            imgui.text_colored(imgui.ImVec4(0.5, 0.5, 0.5, 1.0), "No channels to plot.")
            imgui.text("Add channels with telemetry.watch(...)")
            return

        shown = 0
        for name, channel in channels.items():
            if shown >= self._max_display:
                imgui.text_colored(
                    imgui.ImVec4(0.5, 0.5, 0.5, 1.0),
                    f"... and {len(channels) - shown} more channels",
                )
                break

            values = channel.values
            if not values:
                imgui.text(f"{name}: (no data)")
                shown += 1
                continue

            float_vals: list[float] = []
            for v in values:
                try:
                    float_vals.append(float(v))
                except (TypeError, ValueError):
                    float_vals.append(0.0)

            if not float_vals:
                shown += 1
                continue

            latest = float_vals[-1]
            unit = channel.unit
            unit_str = f" {unit}" if unit else ""
            vmin = min(float_vals)
            vmax = max(float_vals)
            avail_w = imgui.get_content_region_avail().x

            imgui.text_colored(
                imgui.ImVec4(0.7, 0.9, 0.7, 1.0),
                f"{name}: {latest:.4f}{unit_str}  [{vmin:.3f} – {vmax:.3f}]",
            )

            if _HAS_IMPLOT:
                import numpy as np
                y_data = np.array(float_vals, dtype=np.float32)
                # Create an arbitrary x-axis based on length
                x_data = np.arange(len(float_vals), dtype=np.float32)

                if implot.begin_plot(f"##{name}_plot", (avail_w, self._plot_height)):
                    implot.setup_axes("Time (ticks)", unit if unit else "Value")
                    implot.setup_axes_limits(0, max(1, len(x_data) - 1), vmin - abs(vmin) * 0.1 - 1e-6, vmax + abs(vmax) * 0.1 + 1e-6, imgui.Cond_.always.value)
                    
                    implot.plot_line(name, x_data, y_data)
                    implot.end_plot()
            else:
                # Fallback to imgui.plot_lines if implot is not available
                buf = array.array("f", float_vals)
                overlay = f"{latest:.3f}{unit_str}"
                try:
                    imgui.plot_lines(
                        f"##{name}_plot",
                        buf,
                        overlay_text=overlay,
                        scale_min=vmin - abs(vmin) * 0.1 - 1e-6,
                        scale_max=vmax + abs(vmax) * 0.1 + 1e-6,
                        graph_size=(avail_w, max(60.0, self._plot_height / 2)),
                    )
                except Exception:
                    imgui.text(f"{name}: {latest:.4f}{unit_str}")
                    
            imgui.separator()
            shown += 1

    def __repr__(self) -> str:
        return f"PlotsPanel(channels={self._telemetry.channel_names})"

