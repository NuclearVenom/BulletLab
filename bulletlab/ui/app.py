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

# Dear ImGui with GLFW backend
try:
    from imgui_bundle import imgui as _imgui_bundle
    try:
        from imgui_bundle import implot
        _HAS_IMPLOT = True
    except ImportError:
        implot = None
        _HAS_IMPLOT = False

    # glfw: try imgui_bundle's own bundled binding first, then the external package.
    try:
        import imgui_bundle.glfw as glfw  # bundled in some imgui-bundle builds
    except ImportError:
        try:
            import glfw  # external 'glfw' package: pip install glfw
        except ImportError as _glfw_err:
            raise ImportError(
                f"'glfw' package is required for the BulletLab UI.\n"
                f"  Install it with:  pip install glfw\n"
                f"  Original error:   {_glfw_err}"
            ) from _glfw_err

    # GlfwRenderer: try imgui_bundle's python_backends, fall back to OpenGL renderer
    try:
        from imgui_bundle.python_backends.glfw_backend import GlfwRenderer as _GlfwRenderer
    except ImportError:
        from imgui_bundle.python_backends.opengl_backend import OpenGLRenderer as _GlfwRenderer  # type: ignore[assignment]

    import OpenGL.GL as gl

    from imgui_bundle import imgui
    _HAS_IMGUI = True
except ImportError as _imgui_err:
    _HAS_IMGUI = False
    _imgui_bundle = None  # type: ignore[assignment]
    _GlfwRenderer = None  # type: ignore[assignment]
    imgui = None  # type: ignore[assignment]
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
        self._implot_context: Any = None
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
            ImportError: If imgui-bundle is not installed.

        Example::

            app.start()
        """
        if not _HAS_IMGUI:
            _err = getattr(sys.modules[__name__], "_IMGUI_IMPORT_ERROR", "unknown")
            print(
                f"[BulletLab] UI disabled — required packages missing.\n"
                f"  Run:   pip install imgui-bundle glfw PyOpenGL\n"
                f"  Error: {_err}"
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

        # Create ImGui context and initialize the backend renderer.
        # imgui_bundle requires the context to be current before GlfwRenderer
        # builds its device objects (font atlas upload, shader compile).
        self._imgui_context = _imgui_bundle.create_context()
        _imgui_bundle.set_current_context(self._imgui_context)
        
        if _HAS_IMPLOT:
            self._implot_context = implot.create_context()
            implot.set_current_context(self._implot_context)
            
        try:
            self._apply_style()
        except Exception as _style_err:  # pragma: no cover
            import warnings
            warnings.warn(f"[BulletLab] Could not apply custom theme: {_style_err}")


        self._impl = _GlfwRenderer(self._window)

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
        if self._implot_context is not None and _HAS_IMPLOT:
            implot.destroy_context(self._implot_context)
            self._implot_context = None
        self._window = None
        self._impl = None
        self._imgui_context = None

    def _set_window_icon(self, target_window: Any = None) -> None:
        """Load assets/logo.png and set it as the GLFW window icon.

        Silently skips if Pillow is not installed or the file is missing.
        The icon is displayed in the OS taskbar and the window title bar.
        """
        target = target_window or self._window
        if target is None:
            return
        try:
            from PIL import Image
            from pathlib import Path

            # Search: next to this file, then from CWD, then from repo root
            candidates = [
                Path(__file__).parent.parent.parent / "docs" / "assets" / "logo.png",
                Path.cwd() / "docs" / "assets" / "logo.png",
            ]
            icon_path = next((p for p in candidates if p.exists()), None)
            if icon_path is None:
                print(f"[BulletLab] Window icon not found in {candidates[0]} or {candidates[1]}")
                return

            img = Image.open(icon_path).convert("RGBA").resize((64, 64), Image.LANCZOS)
            glfw.set_window_icon(target, 1, [img])
        except Exception as e:
            print(f"[BulletLab] Failed to set window icon: {e}")

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

        # Tick the sequential console script runner (one statement per frame)
        if self._console is not None:
            self._console.tick()

        # Highlighter: reset pending hover before the frame renders
        if self._highlighter is not None:
            self._highlighter.begin_frame()

        _imgui_bundle.new_frame()
        self._render_frame()
        _imgui_bundle.render()

        # Highlighter: commit pending hover → update 3D colours
        if self._highlighter is not None:
            self._highlighter.end_frame()

        gl.glClearColor(0.1, 0.1, 0.12, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self._impl.render(_imgui_bundle.get_draw_data())
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
        imgui.set_next_window_pos(imgui.ImVec2(0, menu_h))
        imgui.set_next_window_size(imgui.ImVec2(w, h - menu_h))
        imgui.begin(
            "##main",
            flags=(
                imgui.WindowFlags_.no_title_bar
                | imgui.WindowFlags_.no_resize
                | imgui.WindowFlags_.no_move
            ),
        )

        # ── Camera panel (shown first when a CameraFollow is registered) ──────
        self._render_camera_panel()

        # ── Custom panels (shown next so they're immediately visible) ────────
        for cp in self._custom_panels:
            label = cp.title
            if imgui.collapsing_header(label, flags=imgui.TreeNodeFlags_.default_open):
                imgui.indent(8)
                cp.render_fn()
                imgui.unindent(8)
            imgui.spacing()

        # ── Built-in panels ──────────────────────────────────────────────────
        if self._show_explorer and self._explorer is not None:
            if imgui.collapsing_header("Explorer", flags=imgui.TreeNodeFlags_.default_open):
                imgui.indent(8)
                self._explorer.render()
                imgui.unindent(8)
            imgui.spacing()

        if self._show_properties and self._properties is not None:
            if self._explorer is not None:
                self._properties.set_target(self._explorer.selected_object)
            if imgui.collapsing_header("Properties", flags=imgui.TreeNodeFlags_.default_open):
                imgui.indent(8)
                self._properties.render()
                imgui.unindent(8)
            imgui.spacing()

        if self._show_telemetry and self._telemetry_panel is not None:
            if imgui.collapsing_header("Telemetry", flags=imgui.TreeNodeFlags_.default_open):
                imgui.indent(8)
                self._telemetry_panel.render()
                imgui.unindent(8)
            imgui.spacing()

        if self._show_plots and self._plots_panel is not None:
            if imgui.collapsing_header("Live Plots", flags=imgui.TreeNodeFlags_.default_open):
                imgui.indent(8)
                if _HAS_IMPLOT and self._implot_context is not None:
                    implot.set_current_context(self._implot_context)
                self._plots_panel.render()
                imgui.unindent(8)
            imgui.spacing()

        if self._show_console and self._console is not None:
            if imgui.collapsing_header("Console", flags=imgui.TreeNodeFlags_.default_open):
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
            _imgui_bundle.set_current_context(self._imgui_context)

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

        self._set_window_icon(self._console_window)

        main_x, main_y = glfw.get_window_pos(self._window)
        glfw.set_window_pos(self._console_window, main_x + 80, main_y + 80)
        glfw.make_context_current(self._console_window)
        glfw.swap_interval(1)

        # Create a *new* independent ImGui context for the console window.
        # imgui-bundle requires explicit context selection before GlfwRenderer
        # initialises its device objects.
        self._console_imgui_context = _imgui_bundle.create_context()
        _imgui_bundle.set_current_context(self._console_imgui_context)
        self._apply_style()
        self._console_impl = _GlfwRenderer(self._console_window)
        # imgui-bundle's GlfwRenderer.char_callback() calls imgui.get_io()
        # which resolves to the *current* context.  Event polling happens
        # while the main context is current, so we override the char callback
        # to switch context before forwarding — identical to the old behaviour.
        glfw.set_char_callback(
            self._console_window,
            self._console_char_callback,
        )
        self._restore_main_context()
        return True

    def _console_char_callback(self, window: Any, codepoint: int) -> None:
        """Route native console text input to its own ImGui context.

        imgui-bundle's GlfwRenderer.char_callback() calls imgui.get_io() which
        resolves to whichever ImGui context is *current* at call time.  We must
        therefore switch to the console context before forwarding and restore
        the main context in the finally block.
        """
        if self._console_impl is None or self._console_imgui_context is None:
            return
        _imgui_bundle.set_current_context(self._console_imgui_context)
        try:
            self._console_impl.char_callback(window, codepoint)
        finally:
            if self._imgui_context is not None:
                _imgui_bundle.set_current_context(self._imgui_context)

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
        _imgui_bundle.set_current_context(self._console_imgui_context)
        self._console_impl.process_inputs()
        _imgui_bundle.new_frame()

        width, height = glfw.get_window_size(self._console_window)
        imgui.set_next_window_pos(imgui.ImVec2(0, 0))
        imgui.set_next_window_size(imgui.ImVec2(width, height))
        imgui.begin(
            "##native_console_host",
            flags=(
                imgui.WindowFlags_.no_title_bar
                | imgui.WindowFlags_.no_resize
                | imgui.WindowFlags_.no_move
                | imgui.WindowFlags_.no_collapse
            ),
        )
        self._console.render_expanded()
        imgui.end()
        _imgui_bundle.render()

        gl.glClearColor(0.1, 0.1, 0.12, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self._console_impl.render(_imgui_bundle.get_draw_data())
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
            _imgui_bundle.set_current_context(self._console_imgui_context)
        if self._console_impl is not None:
            self._console_impl.shutdown()
        if self._console_imgui_context is not None:
            _imgui_bundle.destroy_context(self._console_imgui_context)
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
        if imgui.collapsing_header("Camera", flags=imgui.TreeNodeFlags_.default_open):
            imgui.indent(8)

            # ── Enable / disable toggle (capsule switch) ────────────────────
            from bulletlab.ui import widgets as _ui_widgets
            _ui_widgets.toggle_switch(
                "Dynamic Follow",
                getter=lambda: cam.enabled,
                setter=lambda v: setattr(cam, "enabled", v),
                color_on=(0.2, 0.85, 0.45, 1.0),
                color_off=(0.35, 0.35, 0.35, 1.0),
            )

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
            sim_status = "(Paused)" if self._sim.is_paused else "(Running)"
            imgui.same_line(0, 20)
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
        self._console = ConsolePanel(namespace=ns, sim=self._sim)

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
        """Apply a dark, modern ImGui theme.

        Uses imgui.style_colors_dark() as a base, then overlays custom colours.
        Resilient to imgui-bundle version differences in the Style API.
        """
        from imgui_bundle import imgui as _bi
        from imgui_bundle import ImVec4, ImVec2

        # ── base dark theme ──────────────────────────────────────────────────
        _bi.style_colors_dark()

        style = _bi.get_style()

        # ── colour setter: tries every known API pattern ─────────────────────
        def _sc(col_idx: int, color: ImVec4) -> None:
            """Set one style colour, handling API differences across versions."""
            # imgui-bundle <= 1.4: style.colors is a mutable list
            try:
                style.colors[col_idx] = color
                return
            except (AttributeError, TypeError):
                pass
            # imgui-bundle with capital-C binding
            try:
                style.Colors[col_idx] = color  # type: ignore[index]
                return
            except (AttributeError, TypeError):
                pass
            # imgui-bundle 1.5+ method-based setter
            try:
                style.set_color_(col_idx, color)  # type: ignore[attr-defined]
                return
            except AttributeError:
                pass
            # Final fallback: push_style_color in the frame (handled by caller)

        # ── custom BulletLab colours ─────────────────────────────────────────
        _sc(_bi.Col_.window_bg.value,          ImVec4(0.10, 0.10, 0.13, 0.98))
        _sc(_bi.Col_.title_bg.value,           ImVec4(0.15, 0.15, 0.20, 1.0))
        _sc(_bi.Col_.title_bg_active.value,    ImVec4(0.20, 0.25, 0.35, 1.0))
        _sc(_bi.Col_.button.value,             ImVec4(0.20, 0.40, 0.65, 0.8))
        _sc(_bi.Col_.button_hovered.value,     ImVec4(0.30, 0.55, 0.80, 1.0))
        _sc(_bi.Col_.button_active.value,      ImVec4(0.15, 0.30, 0.55, 1.0))
        _sc(_bi.Col_.frame_bg.value,           ImVec4(0.18, 0.18, 0.22, 1.0))
        _sc(_bi.Col_.frame_bg_hovered.value,   ImVec4(0.22, 0.22, 0.28, 1.0))
        _sc(_bi.Col_.header.value,             ImVec4(0.20, 0.30, 0.45, 0.8))
        _sc(_bi.Col_.header_hovered.value,     ImVec4(0.25, 0.38, 0.55, 1.0))
        _sc(_bi.Col_.header_active.value,      ImVec4(0.15, 0.25, 0.40, 1.0))
        _sc(_bi.Col_.slider_grab.value,        ImVec4(0.40, 0.65, 0.90, 1.0))
        _sc(_bi.Col_.slider_grab_active.value, ImVec4(0.55, 0.80, 1.0,  1.0))
        _sc(_bi.Col_.check_mark.value,         ImVec4(0.40, 0.90, 0.40, 1.0))
        _sc(_bi.Col_.separator.value,          ImVec4(0.30, 0.30, 0.40, 1.0))
        _sc(_bi.Col_.menu_bar_bg.value,        ImVec4(0.12, 0.12, 0.16, 1.0))
        _sc(_bi.Col_.popup_bg.value,           ImVec4(0.12, 0.12, 0.16, 0.98))
        _sc(_bi.Col_.text.value,               ImVec4(0.90, 0.90, 0.95, 1.0))

        # ── sizing (these use named attributes, stable across versions) ───────
        style.window_rounding    = 6.0
        style.frame_rounding     = 4.0
        style.scrollbar_rounding = 4.0
        style.grab_rounding      = 4.0
        style.tab_rounding       = 4.0
        style.window_padding     = ImVec2(10.0, 8.0)
        style.frame_padding      = ImVec2(6.0,  4.0)
        style.item_spacing       = ImVec2(8.0,  6.0)


    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        status = "running" if self._running else "stopped"
        return f"BulletLabUI({self._title!r}, {status})"
