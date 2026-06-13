"""Tests for bulletlab.ui panels and widget helpers (headless/mocked)."""

import pytest


class TestExplorerPanel:
    def test_construct(self, sim):
        from bulletlab.ui.panels.explorer import ExplorerPanel
        panel = ExplorerPanel(sim=sim)
        assert panel is not None

    def test_selected_none_initially(self, sim):
        from bulletlab.ui.panels.explorer import ExplorerPanel
        panel = ExplorerPanel(sim=sim)
        assert panel.selected_object is None

    def test_add_robot(self, sim, r2d2_robot):
        from bulletlab.ui.panels.explorer import ExplorerPanel
        panel = ExplorerPanel(sim=sim)
        panel.add_robot(r2d2_robot)
        assert r2d2_robot in panel._robots

    def test_add_robot_no_duplicates(self, sim, r2d2_robot):
        from bulletlab.ui.panels.explorer import ExplorerPanel
        panel = ExplorerPanel(sim=sim, robots=[r2d2_robot])
        panel.add_robot(r2d2_robot)  # duplicate
        assert panel._robots.count(r2d2_robot) == 1

    def test_on_select_callback(self, sim, r2d2_robot):
        from bulletlab.ui.panels.explorer import ExplorerPanel
        selected = []
        panel = ExplorerPanel(sim=sim, robots=[r2d2_robot], on_select=selected.append)
        panel._select(r2d2_robot)
        assert selected == [r2d2_robot]

    def test_render_without_imgui_does_not_raise(self, sim, r2d2_robot):
        """Render should be a no-op if imgui is not available."""
        from bulletlab.ui.panels.explorer import ExplorerPanel
        import bulletlab.ui.panels.explorer as explorer_mod
        orig = explorer_mod._HAS_IMGUI
        explorer_mod._HAS_IMGUI = False
        panel = ExplorerPanel(sim=sim, robots=[r2d2_robot])
        panel.render()  # should not raise
        explorer_mod._HAS_IMGUI = orig


class TestPropertiesPanel:
    def test_construct(self):
        from bulletlab.ui.panels.properties import PropertiesPanel
        panel = PropertiesPanel()
        assert panel is not None

    def test_set_target_robot(self, r2d2_robot):
        from bulletlab.ui.panels.properties import PropertiesPanel
        panel = PropertiesPanel()
        panel.set_target(r2d2_robot)
        assert panel._target is r2d2_robot

    def test_set_target_none(self):
        from bulletlab.ui.panels.properties import PropertiesPanel
        panel = PropertiesPanel()
        panel.set_target(None)
        assert panel._target is None

    def test_render_without_imgui_does_not_raise(self, r2d2_robot):
        from bulletlab.ui.panels import properties as props_mod
        orig = props_mod._HAS_IMGUI
        props_mod._HAS_IMGUI = False
        from bulletlab.ui.panels.properties import PropertiesPanel
        panel = PropertiesPanel()
        panel.set_target(r2d2_robot)
        panel.render()  # should not raise
        props_mod._HAS_IMGUI = orig


class TestTelemetryPanel:
    def test_construct(self):
        from bulletlab.ui.panels.telemetry import TelemetryPanel
        from bulletlab.telemetry import TelemetryManager
        tm = TelemetryManager()
        panel = TelemetryPanel(tm)
        assert panel is not None

    def test_render_without_imgui_does_not_raise(self):
        from bulletlab.ui.panels import telemetry as tel_mod
        orig = tel_mod._HAS_IMGUI
        tel_mod._HAS_IMGUI = False
        from bulletlab.ui.panels.telemetry import TelemetryPanel
        from bulletlab.telemetry import TelemetryManager
        tm = TelemetryManager()
        tm.watch("x", lambda: 1.0)
        panel = TelemetryPanel(tm)
        panel.render()  # should not raise
        tel_mod._HAS_IMGUI = orig


class TestConsolePanel:
    def test_construct(self):
        from bulletlab.ui.panels.console import ConsolePanel
        panel = ConsolePanel(namespace={"x": 1})
        assert panel is not None

    def test_execute_simple_expression(self):
        from bulletlab.ui.panels.console import ConsolePanel
        panel = ConsolePanel(namespace={})
        panel.execute("1 + 1")
        # Should not raise, should log output
        history_lines = list(panel._history)
        assert any(">>>" in line for line in history_lines)

    def test_execute_assignment(self):
        from bulletlab.ui.panels.console import ConsolePanel
        ns = {}
        panel = ConsolePanel(namespace=ns)
        panel.execute("x = 42")
        assert ns.get("x") == 42

    def test_execute_error_does_not_raise(self):
        from bulletlab.ui.panels.console import ConsolePanel
        panel = ConsolePanel(namespace={})
        panel.execute("raise ValueError('test error')")  # should not propagate

    def test_log_appends_message(self):
        from bulletlab.ui.panels.console import ConsolePanel
        panel = ConsolePanel()
        panel.log("Hello BulletLab")
        assert any("Hello BulletLab" in line for line in panel._history)

    def test_update_namespace(self):
        from bulletlab.ui.panels.console import ConsolePanel
        panel = ConsolePanel(namespace={})
        panel.update_namespace({"robot": "mock"})
        assert panel._namespace["robot"] == "mock"

    def test_render_without_imgui_does_not_raise(self):
        from bulletlab.ui.panels import console as con_mod
        orig = con_mod._HAS_IMGUI
        con_mod._HAS_IMGUI = False
        from bulletlab.ui.panels.console import ConsolePanel
        panel = ConsolePanel()
        panel.render()  # should not raise
        con_mod._HAS_IMGUI = orig


class TestPlotsPanel:
    def test_construct(self):
        from bulletlab.ui.panels.plots import PlotsPanel
        from bulletlab.telemetry import TelemetryManager
        tm = TelemetryManager()
        panel = PlotsPanel(tm)
        assert panel is not None

    def test_render_without_imgui_does_not_raise(self):
        from bulletlab.ui.panels import plots as plots_mod
        orig = plots_mod._HAS_IMGUI
        plots_mod._HAS_IMGUI = False
        from bulletlab.ui.panels.plots import PlotsPanel
        from bulletlab.telemetry import TelemetryManager
        tm = TelemetryManager()
        panel = PlotsPanel(tm)
        panel.render()  # should not raise
        plots_mod._HAS_IMGUI = orig


class TestWidgets:
    """Test widget module functions don't crash when imgui is unavailable."""

    def _disable_imgui(self, widgets_mod) -> bool:
        orig = widgets_mod._HAS_IMGUI
        widgets_mod._HAS_IMGUI = False
        return orig

    def test_button_no_imgui(self):
        import bulletlab.ui.widgets as w
        orig = w._HAS_IMGUI
        w._HAS_IMGUI = False
        result = w.button("Click")
        assert result is False
        w._HAS_IMGUI = orig

    def test_text_no_imgui(self):
        import bulletlab.ui.widgets as w
        orig = w._HAS_IMGUI
        w._HAS_IMGUI = False
        w.text("Label", "value")  # should not raise
        w._HAS_IMGUI = orig

    def test_slider_no_imgui(self):
        import bulletlab.ui.widgets as w
        orig = w._HAS_IMGUI
        w._HAS_IMGUI = False
        result = w.slider("S", 1.0, 0.0, 10.0)
        assert result == 0.0
        w._HAS_IMGUI = orig

    def test_checkbox_no_imgui(self):
        import bulletlab.ui.widgets as w
        orig = w._HAS_IMGUI
        w._HAS_IMGUI = False
        result = w.checkbox("Check", True)
        assert result is False
        w._HAS_IMGUI = orig

    def test_drag_float_no_imgui(self):
        import bulletlab.ui.widgets as w
        orig = w._HAS_IMGUI
        w._HAS_IMGUI = False
        result = w.drag_float("D", 1.0)
        assert result == 0.0
        w._HAS_IMGUI = orig


class TestBulletLabUIConstruction:
    def test_construct_does_not_crash(self, sim, r2d2_robot):
        from bulletlab.ui.app import BulletLabUI
        app = BulletLabUI(sim=sim, robots=[r2d2_robot])
        assert app is not None

    def test_register_panel(self, sim):
        from bulletlab.ui.app import BulletLabUI
        app = BulletLabUI(sim=sim)
        called = []
        app.register_panel("Test Panel", lambda: called.append(True))
        assert len(app._custom_panels) == 1

    def test_custom_panel_decorator(self, sim):
        from bulletlab.ui.app import BulletLabUI
        app = BulletLabUI(sim=sim)

        @app.custom_panel("Decorated Panel")
        def my_panel():
            pass

        assert len(app._custom_panels) == 1
        assert app._custom_panels[0].title == "Decorated Panel"

    def test_not_running_before_start(self, sim):
        from bulletlab.ui.app import BulletLabUI
        app = BulletLabUI(sim=sim)
        assert not app._running

    def test_should_close_false_initially(self, sim):
        from bulletlab.ui.app import BulletLabUI
        app = BulletLabUI(sim=sim)
        assert not app.should_close
