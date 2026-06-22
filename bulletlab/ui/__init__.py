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

import imgui
from bulletlab.robot.joint import _ALL_JOINTS

_original_slider_float = imgui.slider_float

def _patched_slider_float(label: str, *args, **kwargs):
    # Determine if any joint matching the label is pinned
    is_pinned = False
    for j in _ALL_JOINTS:
        if j.is_pinned and (j.name in label or label.startswith(j.name)):
            is_pinned = True
            break
            
    if is_pinned:
        imgui.push_style_color(imgui.COLOR_SLIDER_GRAB, 0.9, 0.2, 0.2, 1.0)
        imgui.push_style_color(imgui.COLOR_SLIDER_GRAB_ACTIVE, 1.0, 0.3, 0.3, 1.0)
        
    res = _original_slider_float(label, *args, **kwargs)
    
    if is_pinned:
        imgui.pop_style_color(2)
        
    return res

imgui.slider_float = _patched_slider_float

__all__ = [
    "BulletLabUI",
    "widgets",
    "ExplorerPanel",
    "PropertiesPanel",
    "TelemetryPanel",
    "ConsolePanel",
    "PlotsPanel",
]
