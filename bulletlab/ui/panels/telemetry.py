"""
TelemetryPanel – displays live robot telemetry data.

Shows all channels registered in a TelemetryManager as a table with
the most recent values. Optionally shows units.

Example::

    from bulletlab.ui.panels.telemetry import TelemetryPanel
    from bulletlab.telemetry import TelemetryManager

    telemetry = TelemetryManager()
    telemetry.watch("Speed", lambda: robot.speed, unit="m/s")

    panel = TelemetryPanel(telemetry)
    panel.render()
"""

from __future__ import annotations

import math
from typing import Any, TYPE_CHECKING

try:
    import imgui

    _HAS_IMGUI = True
except ImportError:  # pragma: no cover
    imgui = None  # type: ignore[assignment]
    _HAS_IMGUI = False

if TYPE_CHECKING:
    from bulletlab.telemetry.manager import TelemetryManager


class TelemetryPanel:
    """Renders a live key-value table of telemetry channel values.

    Args:
        telemetry: The :class:`~bulletlab.telemetry.manager.TelemetryManager` to display.

    Example::

        panel = TelemetryPanel(telemetry)
        # In render loop:
        panel.render()
    """

    def __init__(self, telemetry: "TelemetryManager") -> None:
        self._telemetry = telemetry

    def render(self) -> None:
        """Draw the telemetry panel contents.

        Must be called inside an active ImGui window context.
        """
        if not _HAS_IMGUI:
            return

        if not self._telemetry.channel_names:
            imgui.text_colored("No channels registered.", 0.5, 0.5, 0.5, 1.0)
            imgui.text("Use telemetry.watch(...) to add channels.")
            return

        # Table header
        imgui.columns(3, "telemetry_table", border=True)
        imgui.text("Channel")
        imgui.next_column()
        imgui.text("Value")
        imgui.next_column()
        imgui.text("Unit")
        imgui.next_column()
        imgui.separator()

        for name, channel in self._telemetry.channels.items():
            val = channel.latest
            unit = channel.unit

            imgui.text(name)
            imgui.next_column()

            # Format value
            if val is None:
                val_str = "—"
            elif isinstance(val, float):
                if math.isnan(val):
                    val_str = "NaN"
                elif math.isinf(val):
                    val_str = "Inf"
                else:
                    val_str = f"{val:.4f}"
            elif isinstance(val, (list, tuple)):
                val_str = "(" + ", ".join(f"{v:.3f}" for v in val) + ")"
            else:
                val_str = str(val)

            imgui.text(val_str)
            imgui.next_column()
            imgui.text(unit)
            imgui.next_column()

        imgui.columns(1)

    def __repr__(self) -> str:
        return f"TelemetryPanel(channels={self._telemetry.channel_names})"
