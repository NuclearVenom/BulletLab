"""
ConsolePanel – interactive Python command console in the BulletLab UI.

Provides a compact single-line input, plus an expandable floating window
with a multiline editor and a resizable output area. Commands are executed
via exec() in a configurable namespace, making robot objects and sim directly
accessible.

Single-line mode
    Executes the submitted expression or single statement immediately and
    shows the result, identical to a standard Python REPL.

Multi-line / sequential mode (expanded console)
    When the script contains more than one top-level statement, execution is
    handed to a :class:`~bulletlab.ui.script_runner.ScriptRunner`.  The runner
    executes **one statement per simulation frame**, so each physics change is
    actually rendered before the next command runs.

Built-in console commands (available in every script):

    wait(ms)    Pause the script for *ms* milliseconds (real wall-clock time)
                while the simulation and UI keep running normally.

    step(n=1)   Advance the physics simulation by *n* steps immediately, then
                continue with the next statement.

Example — move joint to 1, hold for 500 ms, return to 0::

    robot.joints['lbr_iiwa_joint_4'].position = 1.0
    wait(500)
    robot.joints['lbr_iiwa_joint_4'].position = 0.0

Example — oscillate a joint five times::

    for _ in range(5):
        robot.joints['lbr_iiwa_joint_4'].position = 1.0
        wait(300)
        robot.joints['lbr_iiwa_joint_4'].position = -1.0
        wait(300)

Note: loops and conditionals are treated as **one statement** by the runner
(the entire for/while/if block executes atomically). To get visible motion
*inside* a loop body, call ``wait()`` or ``step()`` inside the loop.
"""

from __future__ import annotations
from collections import deque
from typing import Any

from bulletlab.console import ConsoleEngine

try:
    import imgui

    _HAS_IMGUI = True
except ImportError:  # pragma: no cover
    imgui = None  # type: ignore[assignment]
    _HAS_IMGUI = False


class ConsolePanel:
    """Interactive Python console panel.

    Executes commands via ``exec()`` in a provided namespace, with output
    captured and displayed in a scrollable log.  When a submitted script
    contains more than one top-level statement it is handed off to the
    internal :class:`~bulletlab.ui.script_runner.ScriptRunner`.

    Args:
        namespace: Dictionary of variables available in the console namespace.
            Typically includes ``sim``, ``robot``, ``telemetry``, etc.
        sim: The active :class:`~bulletlab.core.simulation.Simulation`.
            Required for the ``step()`` built-in and for the runner to tick.
        max_history: Maximum number of output lines to retain.

    Example::

        console = ConsolePanel(namespace={"sim": sim, "robot": robot}, sim=sim)
        console.execute("robot.links['wheel'].mass = 5")
    """

    def __init__(
        self,
        namespace: dict[str, Any] | None = None,
        sim: Any = None,
        max_history: int = 200,
    ) -> None:
        self._history: deque[str] = deque(maxlen=max_history)
        self._input_buf: list[str] = [""]  # mutable for imgui input
        self._scroll_to_bottom: bool = False
        self._focus_input: bool = True
        self._expanded: bool = False
        self._expanded_output_height: float = 260.0

        # Build the sequential script runner (now the full engine)
        self._engine = ConsoleEngine(
            sim=sim,
            on_output=self._history.append,
            on_error=self._on_script_error,
            on_echo=self._history.append,
            on_done=self._on_script_done,
        )

        # Apply any custom namespace values provided to the engine's built namespace
        if namespace:
            self._engine.namespace.update(namespace)

        self._script_error: bool = False
        self._selectable_output: bool = False

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    def update_namespace(self, updates: dict[str, Any]) -> None:
        """Update the console execution namespace."""
        self._engine.namespace.update(updates)

    def tick(self) -> None:
        """Advance the sequential script runner by one statement."""
        if self._engine.is_active:
            self._engine.tick()
            self._scroll_to_bottom = True

    def execute(self, command: str) -> None:
        """Pass the command to the engine for execution."""
        command = command.strip()
        if not command:
            return

        self._script_error = False
        self._engine.execute(command)
        self._scroll_to_bottom = True

    def cancel_script(self) -> None:
        """Abort any currently running sequential script."""
        if self._engine.is_active:
            self._engine.cancel()
            self._history.append("# Terminated by user")
            self._scroll_to_bottom = True

    def log(self, message: str) -> None:
        """Append an informational message to the console log.

        Args:
            message: Text to display in the log.
        """
        self._history.append(f"# {message}")
        self._scroll_to_bottom = True

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self) -> None:
        """Draw the compact console panel contents.

        Must be called inside an active ImGui window context.
        """
        if not _HAS_IMGUI:
            return

        if self._expanded:
            imgui.text_disabled("Console open in separate window")
            return

        if imgui.button("Expand##console_expand"):
            self._expanded = True
            return

        imgui.same_line()
        if imgui.button("Copy Log##console_copy_compact"):
            imgui.set_clipboard_text("\n".join(self._history))

        imgui.same_line()
        changed, val = imgui.checkbox("Select Text##compact", self._selectable_output)
        if changed:
            self._selectable_output = val

        # Ensure status bar doesn't overlap on narrow windows
        avail_x = imgui.get_content_region_available()[0]
        cursor_x = imgui.get_cursor_pos()[0]
        if avail_x > cursor_x + 60:
            self._render_status_bar()
        else:
            imgui.text("")  # Force newline if too tight
            self._render_status_bar()

        self._render_output("console_output", 180.0)
        self._render_single_line_input()

    @property
    def is_expanded(self) -> bool:
        """Whether the console should be shown in its separate window."""
        return self._expanded

    def collapse(self) -> None:
        """Return the console to its compact panel representation."""
        self._expanded = False
        self._focus_input = True

    def render_expanded(self) -> None:
        """Draw expanded console content inside its native host window."""
        if not _HAS_IMGUI or not self._expanded:
            return

        if imgui.button("Collapse##console_collapse"):
            self.collapse()
            return

        imgui.same_line()
        if imgui.button("Copy Log##console_copy_expanded"):
            imgui.set_clipboard_text("\n".join(self._history))

        imgui.same_line()
        changed, val = imgui.checkbox("Select Text##expanded", self._selectable_output)
        if changed:
            self._selectable_output = val

        avail_x = imgui.get_content_region_available()[0]
        cursor_x = imgui.get_cursor_pos()[0]
        if avail_x > cursor_x + 60:
            self._render_status_bar()
        else:
            imgui.text("")
            self._render_status_bar()

        imgui.text_disabled("Drag the divider to resize the output area")

        available = imgui.get_content_region_available()
        max_output_height = max(80.0, float(available[1]) - 150.0)
        self._expanded_output_height = min(
            max(self._expanded_output_height, 80.0),
            max_output_height,
        )

        self._render_output(
            "console_output_expanded",
            self._expanded_output_height,
        )
        self._render_splitter(max_output_height)

        editor_height = max(
            90.0,
            float(imgui.get_content_region_available()[1]) - 34.0,
        )
        if self._focus_input:
            imgui.set_keyboard_focus_here()
            self._focus_input = False

        changed, new_text = imgui.input_text_multiline(
            "##console_multiline_input",
            self._input_buf[0],
            16384,
            width=-1,
            height=editor_height,
            flags=imgui.INPUT_TEXT_ALLOW_TAB_INPUT,
        )
        self._input_buf[0] = new_text

        if imgui.button("Run Code##console_run_multiline"):
            self._submit_input()

    def _render_output(self, child_id: str, height: float) -> None:
        """Render the shared scrollable command history."""
        imgui.begin_child(
            child_id,
            width=0,
            height=height,
            border=True,
        )

        if self._selectable_output:
            full_text = "\n".join(self._history)
            imgui.input_text_multiline(
                "##console_selectable_output",
                full_text,
                max(256, len(full_text) + 1),
                width=-1,
                height=-1,
                flags=imgui.INPUT_TEXT_READ_ONLY,
            )
        else:
            for i, line in enumerate(self._history):
                if line.startswith(">>>"):
                    if "\n" in line:
                        lines = line.split("\n")
                        first_line = lines[0]
                        imgui.push_id(str(i))
                        imgui.push_style_color(imgui.COLOR_TEXT, 0.4, 0.9, 0.4, 1.0)
                        expanded = imgui.tree_node(first_line)
                        
                        if not expanded:
                            imgui.same_line(0, 0)
                            imgui.text(" ...")
                            
                        imgui.pop_style_color()
                        
                        if expanded:
                            for l in lines[1:]:
                                imgui.text_colored(f"    {l}", 0.4, 0.9, 0.4, 1.0)
                            imgui.tree_pop()
                        imgui.pop_id()
                    else:
                        imgui.text_colored(line, 0.4, 0.9, 0.4, 1.0)
                elif line.startswith("  Traceback") or "Error" in line:
                    imgui.text_colored(line, 1.0, 0.3, 0.3, 1.0)
                elif line.startswith("#"):
                    imgui.text_colored(line, 0.6, 0.6, 1.0, 1.0)
                else:
                    imgui.text(line)

        if self._scroll_to_bottom:
            imgui.set_scroll_here_y(1.0)
            self._scroll_to_bottom = False

        imgui.end_child()

    def _render_single_line_input(self) -> None:
        """Render the compact one-line command editor."""
        avail_w = imgui.get_content_region_available()[0]
        run_btn_w = 50
        imgui.push_item_width(avail_w - run_btn_w - 8)
        if self._focus_input:
            imgui.set_keyboard_focus_here()
            self._focus_input = False

        submitted, new_text = imgui.input_text(
            "##console_input",
            self._input_buf[0],
            16384,
            flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE,
        )
        self._input_buf[0] = new_text

        imgui.pop_item_width()
        imgui.same_line()

        if imgui.button("Run##console_run", width=run_btn_w) or submitted:
            self._submit_input()

    def _render_splitter(self, max_output_height: float) -> None:
        """Render the draggable divider below the expanded output log."""
        width = max(1.0, float(imgui.get_content_region_available()[0]))
        imgui.button("##console_output_splitter", width=width, height=7.0)
        if imgui.is_item_active():
            mouse_delta = imgui.get_io().mouse_delta
            self._expanded_output_height = min(
                max(self._expanded_output_height + float(mouse_delta[1]), 80.0),
                max_output_height,
            )

    def _submit_input(self) -> None:
        """Execute and clear the command currently in the shared editor."""
        command = self._input_buf[0].strip()
        if command:
            self.execute(command)
            self._input_buf[0] = ""
            
        self._focus_input = True

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _render_status_bar(self) -> None:
        """Render the status indicator and stop button."""
        if not _HAS_IMGUI:
            return
            
        right_edge = imgui.get_window_content_region_max()[0]
        
        space_needed = 25
        if self._engine.is_active:
            space_needed += 45
            
        cursor_y = imgui.get_cursor_pos()[1]
        imgui.same_line(max(imgui.get_cursor_pos()[0] + 10, right_edge - space_needed))
        
        if self._engine.is_active:
            # Stop button
            imgui.push_style_color(imgui.COLOR_BUTTON, 0.8, 0.2, 0.2, 1.0)
            imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.9, 0.3, 0.3, 1.0)
            imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 1.0, 0.4, 0.4, 1.0)
            if imgui.button("Stop##stop_script"):
                self.cancel_script()
            imgui.pop_style_color(3)
            imgui.same_line()
            
            # Draw blue spinning wheel
            draw_list = imgui.get_window_draw_list()
            pos = imgui.get_cursor_screen_pos()
            center = (pos[0] + 10, pos[1] + 10)
            
            import time, math
            t = time.time() * 8.0
            
            # Draw a spinning arc by drawing a sequence of small circles
            for i in range(4):
                angle = t - i * 0.4
                alpha = 1.0 - i * 0.2
                c = imgui.get_color_u32_rgba(0.2, 0.6, 1.0, alpha)
                draw_list.add_circle_filled(
                    center[0] + math.cos(angle) * 7,
                    center[1] + math.sin(angle) * 7,
                    2.5,
                    c
                )
            imgui.dummy(20, 20)
            
        else:
            # Draw solid dot
            draw_list = imgui.get_window_draw_list()
            pos = imgui.get_cursor_screen_pos()
            center = (pos[0] + 10, pos[1] + 10)
            color = imgui.get_color_u32_rgba(1.0, 0.2, 0.2, 1.0) if self._script_error else imgui.get_color_u32_rgba(0.2, 0.8, 0.2, 1.0)
            draw_list.add_circle_filled(center[0], center[1], 6.0, color)
            imgui.dummy(20, 20)

    def _on_script_error(self, line: str) -> None:
        """Called when the ConsoleEngine hits an error."""
        self._script_error = True
        self._history.append(line)

    def _on_script_done(self) -> None:
        """Called by the ConsoleEngine when the last statement finishes."""
        self._scroll_to_bottom = True

    def __repr__(self) -> str:
        return f"ConsolePanel(history={len(self._history)} lines)"
