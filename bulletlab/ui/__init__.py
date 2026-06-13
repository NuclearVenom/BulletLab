"""
BulletLab UI subpackage.

Provides the ImGui-based control window, all built-in panels, and widget helpers.

Example::

    from bulletlab.ui import BulletLabUI
    from bulletlab.ui import widgets as ui

    app = BulletLabUI(sim=sim, robots=[robot])
    app.run()
"""

from bulletlab.ui.app import BulletLabUI
from bulletlab.ui import widgets
from bulletlab.ui.panels.explorer import ExplorerPanel
from bulletlab.ui.panels.properties import PropertiesPanel
from bulletlab.ui.panels.telemetry import TelemetryPanel
from bulletlab.ui.panels.console import ConsolePanel
from bulletlab.ui.panels.plots import PlotsPanel

__all__ = [
    "BulletLabUI",
    "widgets",
    "ExplorerPanel",
    "PropertiesPanel",
    "TelemetryPanel",
    "ConsolePanel",
    "PlotsPanel",
]
