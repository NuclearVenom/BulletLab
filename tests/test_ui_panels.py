"""Tests for bulletlab.ui panels and widget helpers (headless/mocked)."""

import pytest


class _NoOpProxy:
    """Recursive proxy that absorbs any attribute access and any call.

    Useful as a catch-all in FakeImgui mocks so that chains like
    ``imgui.ChildFlags_.borders`` or ``imgui.ImVec2(0, 0).x`` work
    without manually stubbing every enum / struct.
    """

    def __getattr__(self, name):
        return _NoOpProxy()

    def __call__(self, *args, **kwargs):
        return _NoOpProxy()

    # Make it usable in arithmetic / comparisons / bool contexts
    def __int__(self):
        return 0

    def __float__(self):
        return 0.0

    def __bool__(self):
        return False

    def __index__(self):
        return 0

    # Subscript access (e.g. pos[0])
    def __getitem__(self, key):
        return 0.0

    # Iteration (e.g. for unpacking)
    def __iter__(self):
        return iter([0.0, 0.0])

    def __repr__(self):
        return "_NoOpProxy()"


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

    def test_execute_captures_multiline_output(self):
        from bulletlab.ui.panels.console import ConsolePanel
        panel = ConsolePanel(namespace={})
        panel.execute("for value in range(2):\n    print(value)")
        history = "\n".join(panel._history)
        assert "    0" in history
        assert "    1" in history

    def test_execute_error_does_not_raise(self):
        from bulletlab.ui.panels.console import ConsolePanel
        panel = ConsolePanel(namespace={})
        panel.execute("raise ValueError('test error')")  # should not propagate

    def test_statement_error_does_not_show_eval_probe_error(self):
        from bulletlab.ui.panels.console import ConsolePanel
        panel = ConsolePanel(namespace={})
        panel.execute("missing['key'] = 1")
        history = "\n".join(panel._history)
        assert "NameError" in history
        assert "During handling of the above exception" not in history

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

    @pytest.mark.parametrize("submit_with_enter", [False, True])
    def test_render_submits_input(self, monkeypatch, submit_with_enter):
        from bulletlab.ui.panels import console as con_mod
        from bulletlab.ui.panels.console import ConsolePanel

        class FakeImgui:
            INPUT_TEXT_ENTER_RETURNS_TRUE = 1

            def __init__(self):
                self.focus_calls = 0
                self._input_text_calls = 0

            def __getattr__(self, name):
                if name in ("get_content_region_available", "get_content_region_avail"):
                    return lambda: type("ImVec2", (), {"x": 300.0, "y": 300.0})()
                if name in ("get_cursor_pos", "get_cursor_screen_pos"):
                    return lambda: type("ImVec2", (), {"x": 0.0, "y": 0.0})()
                if name == "get_window_draw_list":
                    _dl = type("DrawList", (), {"__getattr__": lambda s, n: (lambda *a, **k: None)})()
                    return lambda: _dl
                if name == "input_text":
                    return self._input_text
                if name == "button":
                    # Run button fires on first render only (mirrors enter-key submit toggle)
                    return lambda label, *args, **kwargs: (
                        label.startswith("Run##")
                        and not submit_with_enter
                        and self._input_text_calls <= 1
                    )
                if name == "set_keyboard_focus_here":
                    return self._set_focus
                return _NoOpProxy()

            def _input_text(self, *args, **kwargs):
                self._input_text_calls += 1
                if self._input_text_calls == 1:
                    # First render: simulate user having typed "x = 42" and pressing Enter
                    return (submit_with_enter, "x = 42")
                # Subsequent renders: widget is empty (buffer was cleared after submit)
                return (False, "")

            def _set_focus(self):
                self.focus_calls += 1

        fake_imgui = FakeImgui()
        monkeypatch.setattr(con_mod, "imgui", fake_imgui)
        monkeypatch.setattr(con_mod, "_HAS_IMGUI", True)

        namespace = {}
        panel = ConsolePanel(namespace=namespace)
        panel.render()

        assert namespace["x"] == 42
        assert panel._input_buf == [""]
        assert panel._focus_input is True

        # Next frame consumes the focus request
        panel.render()
        assert fake_imgui.focus_calls == 1
        assert panel._focus_input is False

    def test_expanded_console_runs_multiline_and_resizes_output(self, monkeypatch):
        from bulletlab.ui.panels import console as con_mod
        from bulletlab.ui.panels.console import ConsolePanel

        class FakeImgui:
            INPUT_TEXT_ALLOW_TAB_INPUT = 2

            def __getattr__(self, name):
                if name in ("get_content_region_available", "get_content_region_avail"):
                    return lambda: type("ImVec2", (), {"x": 600.0, "y": 500.0})()
                if name in ("get_cursor_pos", "get_cursor_screen_pos"):
                    return lambda: type("ImVec2", (), {"x": 0.0, "y": 0.0})()
                if name == "get_window_draw_list":
                    _dl = type("DrawList", (), {"__getattr__": lambda s, n: (lambda *a, **k: None)})()
                    return lambda: _dl
                if name == "input_text_multiline":
                    return lambda *args, **kwargs: (
                        True,
                        "for value in range(3):\n    total = value",
                    )
                if name == "button":
                    return lambda label, *args, **kwargs: label.startswith("Run Code")
                if name == "is_item_active":
                    return lambda: True
                if name == "get_io":
                    return lambda: type("IO", (), {"mouse_delta": (0, 25)})()
                return _NoOpProxy()

        monkeypatch.setattr(con_mod, "imgui", FakeImgui())
        monkeypatch.setattr(con_mod, "_HAS_IMGUI", True)

        namespace = {}
        panel = ConsolePanel(namespace=namespace)
        panel._expanded = True
        panel.render_expanded()

        assert namespace["total"] == 2
        assert panel._input_buf == [""]
        assert panel._expanded_output_height == 285.0

    def test_expand_button_hidden_while_console_is_expanded(self, monkeypatch):
        from bulletlab.ui.panels import console as con_mod
        from bulletlab.ui.panels.console import ConsolePanel

        button_labels = []

        class FakeImgui:
            INPUT_TEXT_ENTER_RETURNS_TRUE = 1

            def button(self, label, *args, **kwargs):
                button_labels.append(label)
                return False

            def text_disabled(self, *args, **kwargs):
                pass

            def __getattr__(self, name):
                if name in ("get_content_region_available", "get_content_region_avail"):
                    return lambda: type("ImVec2", (), {"x": 300.0, "y": 300.0})()
                if name in ("get_cursor_pos", "get_cursor_screen_pos"):
                    return lambda: type("ImVec2", (), {"x": 0.0, "y": 0.0})()
                if name == "get_window_draw_list":
                    _dl = type("DrawList", (), {"__getattr__": lambda s, n: (lambda *a, **k: None)})()
                    return lambda: _dl
                if name == "input_text":
                    return lambda *args, **kwargs: (False, "")
                return _NoOpProxy()

        monkeypatch.setattr(con_mod, "imgui", FakeImgui())
        monkeypatch.setattr(con_mod, "_HAS_IMGUI", True)

        panel = ConsolePanel()
        panel._expanded = True
        panel.render()
        assert not any(label.startswith("Expand") for label in button_labels)

        panel.collapse()
        panel.render()
        assert any(label.startswith("Expand") for label in button_labels)


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
