"""
BulletLab UI subpackage.

Provides the ImGui-based control window, all built-in panels, and widget helpers.

Example::

    from bulletlab.ui import BulletLabUI
    from bulletlab.ui import widgets as ui

    app = BulletLabUI(sim=sim, robots=[robot])
    app.run()
"""

# ---------------------------------------------------------------------------
# Guard ALL UI imports so that  `from bulletlab.ui import BulletLabUI`
# never raises ImportError even when imgui-bundle / glfw are absent.
# When unavailable we expose a lightweight _DisabledUI stub.
# ---------------------------------------------------------------------------

_UI_IMPORT_ERROR: str | None = None

try:
    from bulletlab.ui.app import BulletLabUI as _RealBulletLabUI
    from bulletlab.ui import widgets
    from bulletlab.ui.panels.explorer import ExplorerPanel
    from bulletlab.ui.panels.properties import PropertiesPanel
    from bulletlab.ui.panels.telemetry import TelemetryPanel
    from bulletlab.ui.panels.console import ConsolePanel
    from bulletlab.ui.panels.plots import PlotsPanel

    from bulletlab.ui.panels.plots import PlotsPanel

    # -------------------------------------------------------------------------
    # imgui.slider_float monkey-patch
    # -------------------------------------------------------------------------
    try:
        from imgui_bundle import imgui
        from bulletlab.robot.joint import _ALL_JOINTS

        _original_slider_float = imgui.slider_float

        def _patched_slider_float(label: str, *args, **kwargs):
            is_pinned = False
            for j in _ALL_JOINTS:
                if j.is_pinned and (j.name in label or label.startswith(j.name)):
                    is_pinned = True
                    break

            if is_pinned:
                imgui.push_style_color(imgui.Col_.slider_grab, imgui.ImVec4(0.9, 0.2, 0.2, 1.0))
                imgui.push_style_color(imgui.Col_.slider_grab_active, imgui.ImVec4(1.0, 0.3, 0.3, 1.0))

            res = _original_slider_float(label, *args, **kwargs)

            if is_pinned:
                imgui.pop_style_color(2)
            return res

        imgui.slider_float = _patched_slider_float
    except ImportError:
        pass  # imgui-bundle compat layer not available; slider patch skipped

    BulletLabUI = _RealBulletLabUI

except ImportError as _e:
    _UI_IMPORT_ERROR = str(_e)

    # ------------------------------------------------------------------
    # Stub — keeps  `from bulletlab.ui import BulletLabUI`  from raising.
    # All panel types and widgets resolve to no-op dummies.
    # ------------------------------------------------------------------
    class BulletLabUI:  # type: ignore[no-redef]
        """Disabled stub — imgui-bundle or glfw not installed."""

        def __init__(self, *args, **kwargs):
            import sys as _sys
            print(
                f"[BulletLab] UI disabled — required packages missing.\n"
                f"  Run:   pip install imgui-bundle glfw PyOpenGL\n"
                f"  Error: {_UI_IMPORT_ERROR}",
                file=_sys.stderr,
            )

        def start(self): return self
        def stop(self): return self
        def run(self): return self
        def update(self): pass
        def custom_panel(self, *a, **kw):
            """No-op decorator — panel is silently skipped."""
            def _decorator(fn):
                return fn
            return _decorator
        def __bool__(self): return False

    class _DummyPanel:
        def __init__(self, *a, **kw): pass
        def render(self): pass

    ExplorerPanel  = _DummyPanel  # type: ignore[assignment]
    PropertiesPanel = _DummyPanel  # type: ignore[assignment]
    TelemetryPanel = _DummyPanel   # type: ignore[assignment]
    ConsolePanel   = _DummyPanel   # type: ignore[assignment]
    PlotsPanel     = _DummyPanel   # type: ignore[assignment]

    class _DummyWidgets:
        def __getattr__(self, name):
            return lambda *a, **kw: None

    widgets = _DummyWidgets()  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# imgui — expose it so examples can do:  from bulletlab.ui import imgui
# ---------------------------------------------------------------------------
try:
    from imgui_bundle import imgui
except ImportError:
    imgui = None  # type: ignore[assignment]


__all__ = [
    "BulletLabUI",
    "widgets",
    "imgui",
    "ExplorerPanel",
    "PropertiesPanel",
    "TelemetryPanel",
    "ConsolePanel",
    "PlotsPanel",
]
