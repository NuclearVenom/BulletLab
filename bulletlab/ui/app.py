"""
BulletLabUI – the main ImGui control window for BulletLab.

Opens a separate Dear ImGui window (using GLFW + OpenGL backend) alongside
the PyBullet simulation window. All built-in panels are shown by default;
custom panels can be added via decorators or direct registration.

Architecture note:
    This window is completely independent of PyBullet's renderer.
    PyBullet handles physics + 3D visualization.
    BulletLabUI handles parameter editing, telemetry, and console.

Example::

    from bulletlab.ui import BulletLabUI

    app = BulletLabUI(sim=sim, robots=[robot], telemetry=telemetry)
    app.run()    # blocking

Non-blocking step mode::

    app = BulletLabUI(sim=sim, robots=[robot])
    app.start()
    while True:
        sim.step()
        telemetry.update(t=sim.elapsed_time)
        app.step()   # render one ImGui frame
        if app.should_close:
            break
    app.stop()
"""

from __future__ import annotations

import sys
from typing import Any, Callable, TYPE_CHECKING

# ImGui with GLFW backend
try:
    import imgui
    import imgui.integrations.glfw as imgui_glfw
    import glfw
    import OpenGL.GL as gl

    _HAS_IMGUI = True
except ImportError as _imgui_err:  # pragma: no cover
    _HAS_IMGUI = False
    imgui = None  # type: ignore[assignment]
    imgui_glfw = None  # type: ignore[assignment]
    glfw = None  # type: ignore[assignment]
    gl = None  # type: ignore[assignment]
    _IMGUI_IMPORT_ERROR = str(_imgui_err)

from bulletlab.ui.panels.explorer import ExplorerPanel
from bulletlab.ui.panels.properties import PropertiesPanel
from bulletlab.ui.panels.telemetry import TelemetryPanel
from bulletlab.ui.panels.console import ConsolePanel
from bulletlab.ui.panels.plots import PlotsPanel

if TYPE_CHECKING:
    from bulletlab.core.simulation import Simulation
    from bulletlab.robot.robot import Robot
    from bulletlab.telemetry.manager import TelemetryManager


class _CustomPanel:
    """Container for a user-defined panel."""

    def __init__(self, title: str, render_fn: Callable[[], None]) -> None:
        self.title = title
        self.render_fn = render_fn


class BulletLabUI:
    """Main ImGui control window for BulletLab.

    Opens a GLFW + OpenGL window with Dear ImGui. Provides five built-in
    panels (Explorer, Properties, Telemetry, Console, Plots) and allows
    registering custom panels via :meth:`custom_panel` decorator or
    :meth:`register_panel`.

    Args:
        sim: The :class:`~bulletlab.core.simulation.Simulation` instance.
        robots: List of robots to display in the UI.
        telemetry: Optional :class:`~bulletlab.telemetry.manager.TelemetryManager`.
        width: Initial window width in pixels.
        height: Initial window height in pixels.
        title: Window title.

    Example::

        app = BulletLabUI(sim=sim, robots=[robot], telemetry=telemetry)
        app.run()
    """

    def __init__(
        self,
        sim: "Simulation",
        robots: list["Robot"] | None = None,
        telemetry: "TelemetryManager | None" = None,
        camera: "Any | None" = None,
        highlighter: "Any | None" = None,
        width: int = 600,
        height: int = 800,
        title: str = "BulletLab",
    ) -> None:
        self._sim = sim
        self._robots: list["Robot"] = list(robots or [])
        self._telemetry = telemetry
        self._camera = camera          # CameraFollow instance (optional)
        self._highlighter = highlighter  # RobotHighlighter instance (optional)
        self._width = width
        self._height = height
        self._title = title

        self._window: Any = None
        self._impl: Any = None
        self._imgui_context: Any = None
        self._console_window: Any = None
        self._console_impl: Any = None
        self._console_imgui_context: Any = None
        self._running = False
        self._should_close = False

        # Built-in panels
        self._explorer: ExplorerPanel | None = None
        self._properties: PropertiesPanel | None = None
        self._telemetry_panel: TelemetryPanel | None = None
        self._console: ConsolePanel | None = None
        self._plots_panel: PlotsPanel | None = None

        # Custom panels
        self._custom_panels: list[_CustomPanel] = []

        # Panel visibility flags
        self._show_explorer = True
        self._show_properties = True
        self._show_telemetry = True
        self._show_console = True
        self._show_plots = True

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> "BulletLabUI":
        """Initialize the GLFW window and ImGui context.

        Returns:
            self, for method chaining.

        Raises:
            ImportError: If pyimgui[glfw] or glfw is not installed.

        Example::

            app.start()
        """
        if not _HAS_IMGUI:
            print(
                f"[BulletLab] UI disabled: pyimgui[glfw] not available.\n"
                f"  Install with: pip install imgui[glfw]\n"
                f"  Error: {getattr(sys.modules[__name__], '_IMGUI_IMPORT_ERROR', 'unknown')}"
            )
            return self

        if self._running:
            return self

        # Init GLFW
        if not glfw.init():
            raise RuntimeError("GLFW initialization failed.")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

        self._window = glfw.create_window(
            self._width, self._height, self._title, None, None
        )
        if not self._window:
            glfw.terminate()
            raise RuntimeError("Failed to create GLFW window.")

        # Set window icon from assets/logo.png
        self._set_window_icon()

        glfw.make_context_current(self._window)
        glfw.swap_interval(1)  # vsync

        # Style ImGui
        self._imgui_context = imgui.create_context()
        self._apply_style()

        self._impl = imgui_glfw.GlfwRenderer(self._window)

        # Build panels
        self._build_panels()
        self._running = True
        return self

    def stop(self) -> None:
        """Shut down the ImGui window and free GLFW resources.

        Example::

            app.stop()
        """
        if not self._running:
            return
        self._running = False
        self._close_console_window()
        if self._impl is not None:
            self._restore_main_context()
            self._impl.shutdown()
        if self._window is not None and glfw is not None:
            glfw.destroy_window(self._window)
            glfw.terminate()
        self._window = None
        self._impl = None
        self._imgui_context = None

    def _set_window_icon(self) -> None:
        """Load assets/logo.png and set it as the GLFW window icon.

        Silently skips if Pillow is not installed or the file is missing.
        The icon is displayed in the OS taskbar and the window title bar.
        """
        try:
            from PIL import Image
            import numpy as np
            from pathlib import Path

            # Search: next to this file, then from CWD, then from repo root
            candidates = [
                Path(__file__).parent.parent.parent / "assets" / "logo.png",
                Path.cwd() / "assets" / "logo.png",
            ]
            icon_path = next((p for p in candidates if p.exists()), None)
            if icon_path is None:
                return

            img = Image.open(icon_path).convert("RGBA").resize((64, 64), Image.LANCZOS)
            pixels = np.array(img, dtype=np.uint8)
            glfw.set_window_icon(self._window, 1, [pixels])
        except Exception:
            pass   # non-fatal — icon is cosmetic only

    # ------------------------------------------------------------------
    # Main loops
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the BulletLabUI event loop (blocking).

        This loop runs until the window is closed. For non-blocking usage,
        call :meth:`start` and then :meth:`step` in your own simulation loop.

        Example::

            app.run()
        """
        self.start()
        if not _HAS_IMGUI or not self._running:
            return

        while not glfw.window_should_close(self._window):
            self.step()

        self.stop()

    def step(self) -> None:
        """Render one ImGui frame.

        Call this once per simulation step in your own loop.

        Example::

            while True:
                sim.step()
                telemetry.update(t=sim.elapsed_time)
                app.step()
                if app.should_close:
                    break
        """
        if not _HAS_IMGUI or not self._running:
            return

        if glfw.window_should_close(self._window):
            self._should_close = True
            return

        self._restore_main_context()
        glfw.poll_events()
        self._impl.process_inputs()

        # Highlighter: reset pending hover before the frame renders
        if self._highlighter is not None:
            self._highlighter.begin_frame()

        imgui.new_frame()
        self._render_frame()
        imgui.render()

        # Highlighter: commit pending hover → update 3D colours
        if self._highlighter is not None:
            self._highlighter.end_frame()

        gl.glClearColor(0.1, 0.1, 0.12, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self._impl.render(imgui.get_draw_data())
        glfw.swap_buffers(self._window)
        self._render_console_window()

    @property
    def should_close(self) -> bool:
        """``True`` if the UI window has been closed by the user."""
        return self._should_close

    # ------------------------------------------------------------------
    # Frame rendering
    # ------------------------------------------------------------------

    def _render_frame(self) -> None:
        """Render all panels inside a single full-screen ImGui window."""
        self._render_main_menu()

        w, h = glfw.get_window_size(self._window)
        menu_h = 20  # approx height of the main menu bar

        # One full-screen, non-movable, non-resizable window that fills the
        # entire GLFW client area below the menu bar.
        imgui.set_next_window_position(0, menu_h)
        imgui.set_next_window_size(w, h - menu_h)
        imgui.begin(
            "##main",
            flags=(
                imgui.WINDOW_NO_TITLE_BAR
                | imgui.WINDOW_NO_RESIZE
                | imgui.WINDOW_NO_MOVE
            ),
        )

        # ── Camera panel (shown first when a CameraFollow is registered) ──────
        self._render_camera_panel()

        # ── Custom panels (shown next so they're immediately visible) ────────
        for cp in self._custom_panels:
            label = cp.title
            if imgui.collapsing_header(label, flags=imgui.TREE_NODE_DEFAULT_OPEN)[0]:
                imgui.indent(8)
                cp.render_fn()
                imgui.unindent(8)
            imgui.spacing()

        # ── Built-in panels ──────────────────────────────────────────────────
        if self._show_explorer and self._explorer is not None:
            if imgui.collapsing_header("Explorer", flags=imgui.TREE_NODE_DEFAULT_OPEN)[0]:
                imgui.indent(8)
                self._explorer.render()
                imgui.unindent(8)
            imgui.spacing()

        if self._show_properties and self._properties is not None:
            if self._explorer is not None:
                self._properties.set_target(self._explorer.selected_object)
            if imgui.collapsing_header("Properties", flags=imgui.TREE_NODE_DEFAULT_OPEN)[0]:
                imgui.indent(8)
                self._properties.render()
                imgui.unindent(8)
            imgui.spacing()

        if self._show_telemetry and self._telemetry_panel is not None:
            if imgui.collapsing_header("Telemetry", flags=imgui.TREE_NODE_DEFAULT_OPEN)[0]:
                imgui.indent(8)
                self._telemetry_panel.render()
                imgui.unindent(8)
            imgui.spacing()

        if self._show_plots and self._plots_panel is not None:
            if imgui.collapsing_header("Live Plots", flags=imgui.TREE_NODE_DEFAULT_OPEN)[0]:
                imgui.indent(8)
                self._plots_panel.render()
                imgui.unindent(8)
            imgui.spacing()

        if self._show_console and self._console is not None:
            if imgui.collapsing_header("Console", flags=imgui.TREE_NODE_DEFAULT_OPEN)[0]:
                imgui.indent(8)
                self._console.render()
                imgui.unindent(8)
            imgui.spacing()

        imgui.end()

    # ------------------------------------------------------------------
    # Native console window
    # ------------------------------------------------------------------

    def _restore_main_context(self) -> None:
        """Make the main GLFW and ImGui contexts current."""
        if self._window is not None:
            glfw.make_context_current(self._window)
        if self._imgui_context is not None:
            imgui.set_current_context(self._imgui_context)

    def _open_console_window(self) -> bool:
        """Create the separate native window used by the expanded console."""
        if self._console_window is not None:
            return True

        self._console_window = glfw.create_window(
            900, 650, "BulletLab Console", None, self._window
        )
        if not self._console_window:
            self._console_window = None
            if self._console is not None:
                self._console.log("Could not create the separate console window.")
                self._console.collapse()
            self._restore_main_context()
            return False

        main_x, main_y = glfw.get_window_pos(self._window)
        glfw.set_window_pos(self._console_window, main_x + 80, main_y + 80)
        glfw.make_context_current(self._console_window)
        glfw.swap_interval(1)

        self._console_imgui_context = imgui.create_context()
        # ImGui only makes a newly created context current when no context
        # already exists. Select it explicitly before the renderer builds its
        # device objects and font atlas.
        imgui.set_current_context(self._console_imgui_context)
        self._apply_style()
        self._console_impl = imgui_glfw.GlfwRenderer(self._console_window)
        # pyimgui's GLFW character callback looks up the current global ImGui
        # context. Event polling happens while the main context is current, so
        # route text input explicitly to the console context.
        glfw.set_char_callback(
            self._console_window,
            self._console_char_callback,
        )
        self._restore_main_context()
        return True

    def _console_char_callback(self, window: Any, codepoint: int) -> None:
        """Route native console text input to its own ImGui context."""
        if self._console_impl is None or self._console_imgui_context is None:
            return
        imgui.set_current_context(self._console_imgui_context)
        try:
            self._console_impl.char_callback(window, codepoint)
        finally:
            if self._imgui_context is not None:
                imgui.set_current_context(self._imgui_context)

    def _render_console_window(self) -> None:
        """Render one frame of the expanded console's native window."""
        if self._console is None or not self._console.is_expanded:
            self._close_console_window()
            return

        if not self._open_console_window():
            return

        if glfw.window_should_close(self._console_window):
            self._console.collapse()
            self._close_console_window()
            return

        glfw.make_context_current(self._console_window)
        imgui.set_current_context(self._console_imgui_context)
        self._console_impl.process_inputs()
        imgui.new_frame()

        width, height = glfw.get_window_size(self._console_window)
        imgui.set_next_window_position(0, 0)
        imgui.set_next_window_size(width, height)
        imgui.begin(
            "##native_console_host",
            flags=(
                imgui.WINDOW_NO_TITLE_BAR
                | imgui.WINDOW_NO_RESIZE
                | imgui.WINDOW_NO_MOVE
                | imgui.WINDOW_NO_COLLAPSE
            ),
        )
        self._console.render_expanded()
        imgui.end()
        imgui.render()

        gl.glClearColor(0.1, 0.1, 0.12, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self._console_impl.render(imgui.get_draw_data())
        glfw.swap_buffers(self._console_window)

        if not self._console.is_expanded:
            self._close_console_window()
        else:
            self._restore_main_context()

    def _close_console_window(self) -> None:
        """Destroy the native console window and its ImGui resources."""
        if self._console_window is None:
            return

        glfw.make_context_current(self._console_window)
        if self._console_imgui_context is not None:
            imgui.set_current_context(self._console_imgui_context)
        if self._console_impl is not None:
            self._console_impl.shutdown()
        if self._console_imgui_context is not None:
            imgui.destroy_context(self._console_imgui_context)
        glfw.destroy_window(self._console_window)

        self._console_window = None
        self._console_impl = None
        self._console_imgui_context = None
        self._restore_main_context()

    def _render_camera_panel(self) -> None:
        """Render the built-in Camera Follow control panel.

        Only visible when a :class:`~bulletlab.core.camera.CameraFollow`
        was passed to the constructor via ``camera=``.
        """
        if self._camera is None:
            return

        cam = self._camera
        if imgui.collapsing_header("Camera", flags=imgui.TREE_NODE_DEFAULT_OPEN)[0]:
            imgui.indent(8)

            # ── Enable / disable toggle ─────────────────────────────────────
            changed, new_val = imgui.checkbox("Dynamic Follow", cam.enabled)
            if changed:
                cam.enabled = new_val
            imgui.same_line(spacing=12)
            status = "ON" if cam.enabled else "OFF"
            color  = (0.3, 0.9, 0.4, 1.0) if cam.enabled else (0.6, 0.6, 0.6, 1.0)
            imgui.text_colored(f"[{status}]", *color)

            if cam.enabled:
                imgui.spacing()

                # ── Mode label ──────────────────────────────────────────────
                imgui.text(f"Mode:  {cam.mode}")

                # ── Distance slider ──────────────────────────────────────────
                changed, val = imgui.slider_float(
                    "Distance", cam.distance, 1.0, 20.0, "%.1f m"
                )
                if changed:
                    cam.distance = val

                # ── Lerp / smoothness slider ─────────────────────────────────
                if cam.mode in ("smooth", "chase"):
                    changed, val = imgui.slider_float(
                        "Smoothness", 1.0 - cam.lerp, 0.0, 0.99, "%.2f"
                    )
                    if changed:
                        cam.lerp = 1.0 - val   # invert: high = smoother

                # ── Pitch slider ─────────────────────────────────────────────
                changed, val = imgui.slider_float(
                    "Pitch", cam.pitch, -89.0, 0.0, "%.0f°"
                )
                if changed:
                    cam.pitch = val

            imgui.unindent(8)
        imgui.spacing()

    def _render_main_menu(self) -> None:
        """Render the main menu bar."""
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("View"):
                _, self._show_explorer = imgui.menu_item(
                    "Explorer", selected=self._show_explorer
                )
                _, self._show_properties = imgui.menu_item(
                    "Properties", selected=self._show_properties
                )
                _, self._show_telemetry = imgui.menu_item(
                    "Telemetry", selected=self._show_telemetry
                )
                _, self._show_plots = imgui.menu_item(
                    "Plots", selected=self._show_plots
                )
                _, self._show_console = imgui.menu_item(
                    "Console", selected=self._show_console
                )
                imgui.end_menu()

            if imgui.begin_menu("Simulation"):
                if imgui.menu_item("Pause")[0] and not self._sim.is_paused:
                    self._sim.pause()
                if imgui.menu_item("Resume")[0] and self._sim.is_paused:
                    self._sim.resume()
                if imgui.menu_item("Reset")[0]:
                    self._sim.reset()
                imgui.end_menu()

            # Status bar
            sim_status = "⏸ Paused" if self._sim.is_paused else "▶ Running"
            imgui.same_line(spacing=20)
            imgui.text(
                f"  {sim_status}  |  "
                f"Step: {self._sim.step_count}  |  "
                f"t={self._sim.elapsed_time:.2f}s  |  "
                f"Robots: {len(self._robots)}"
            )

            imgui.end_main_menu_bar()

    # ------------------------------------------------------------------
    # Panel management
    # ------------------------------------------------------------------

    def _build_panels(self) -> None:
        """Instantiate all built-in panels."""
        self._explorer = ExplorerPanel(
            sim=self._sim,
            robots=self._robots,
            highlighter=self._highlighter,
        )
        self._properties = PropertiesPanel(highlighter=self._highlighter)

        if self._telemetry is not None:
            self._telemetry_panel = TelemetryPanel(self._telemetry)
            self._plots_panel = PlotsPanel(self._telemetry)
        else:
            # Create empty telemetry so panels render gracefully
            from bulletlab.telemetry import TelemetryManager
            _empty = TelemetryManager()
            self._telemetry_panel = TelemetryPanel(_empty)
            self._plots_panel = PlotsPanel(_empty)

        ns = {"sim": self._sim}
        for i, r in enumerate(self._robots):
            ns[r.name] = r
            if i == 0:
                ns["robot"] = r
        if self._telemetry is not None:
            ns["telemetry"] = self._telemetry
        self._console = ConsolePanel(namespace=ns)

    def register_panel(self, title: str, render_fn: Callable[[], None]) -> None:
        """Register a custom panel.

        Args:
            title: Panel window title.
            render_fn: Function that renders the panel content using
                ``bulletlab.ui.widgets`` or raw imgui calls.

        Example::

            def my_controls():
                ui.button("Reset", robot.reset)
                ui.slider("Speed", lambda: target_speed, 0, 20,
                          setter=lambda v: set_target_speed(v))

            app.register_panel("My Controls", my_controls)
        """
        self._custom_panels.append(_CustomPanel(title=title, render_fn=render_fn))

    def custom_panel(self, title: str) -> Callable[[Callable[[], None]], Callable[[], None]]:
        """Decorator for registering a custom panel.

        Args:
            title: Panel window title.

        Returns:
            Decorator that registers the function as a panel.

        Example::

            @app.custom_panel("My Controls")
            def my_controls():
                ui.button("Reset", robot.reset)
        """
        def decorator(fn: Callable[[], None]) -> Callable[[], None]:
            self.register_panel(title, fn)
            return fn
        return decorator

    def add_robot(self, robot: "Robot") -> None:
        """Add a robot to the UI (explorer and console namespace).

        Args:
            robot: The robot to add.
        """
        if robot not in self._robots:
            self._robots.append(robot)
        if self._explorer is not None:
            self._explorer.add_robot(robot)
        if self._console is not None:
            self._console.update_namespace({robot.name: robot, "robot": robot})

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _apply_style(self) -> None:
        """Apply a dark, modern ImGui theme."""
        style = imgui.get_style()

        # Colors
        style.colors[imgui.COLOR_WINDOW_BACKGROUND] = (0.10, 0.10, 0.13, 0.98)
        style.colors[imgui.COLOR_TITLE_BACKGROUND] = (0.15, 0.15, 0.20, 1.0)
        style.colors[imgui.COLOR_TITLE_BACKGROUND_ACTIVE] = (0.20, 0.25, 0.35, 1.0)
        style.colors[imgui.COLOR_BUTTON] = (0.20, 0.40, 0.65, 0.8)
        style.colors[imgui.COLOR_BUTTON_HOVERED] = (0.30, 0.55, 0.80, 1.0)
        style.colors[imgui.COLOR_BUTTON_ACTIVE] = (0.15, 0.30, 0.55, 1.0)
        style.colors[imgui.COLOR_FRAME_BACKGROUND] = (0.18, 0.18, 0.22, 1.0)
        style.colors[imgui.COLOR_FRAME_BACKGROUND_HOVERED] = (0.22, 0.22, 0.28, 1.0)
        style.colors[imgui.COLOR_HEADER] = (0.20, 0.30, 0.45, 0.8)
        style.colors[imgui.COLOR_HEADER_HOVERED] = (0.25, 0.38, 0.55, 1.0)
        style.colors[imgui.COLOR_HEADER_ACTIVE] = (0.15, 0.25, 0.40, 1.0)
        style.colors[imgui.COLOR_SLIDER_GRAB] = (0.40, 0.65, 0.90, 1.0)
        style.colors[imgui.COLOR_SLIDER_GRAB_ACTIVE] = (0.55, 0.80, 1.0, 1.0)
        style.colors[imgui.COLOR_CHECK_MARK] = (0.40, 0.90, 0.40, 1.0)
        style.colors[imgui.COLOR_SEPARATOR] = (0.30, 0.30, 0.40, 1.0)
        style.colors[imgui.COLOR_MENUBAR_BACKGROUND] = (0.12, 0.12, 0.16, 1.0)
        style.colors[imgui.COLOR_POPUP_BACKGROUND] = (0.12, 0.12, 0.16, 0.98)
        style.colors[imgui.COLOR_TEXT] = (0.90, 0.90, 0.95, 1.0)

        # Sizing
        style.window_rounding = 6.0
        style.frame_rounding = 4.0
        style.scrollbar_rounding = 4.0
        style.grab_rounding = 4.0
        style.tab_rounding = 4.0
        style.window_padding = (10.0, 8.0)
        style.frame_padding = (6.0, 4.0)
        style.item_spacing = (8.0, 6.0)

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        status = "running" if self._running else "stopped"
        return f"BulletLabUI({self._title!r}, {status})"
