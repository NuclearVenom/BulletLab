"""
ConsolePanel – interactive Python command console in the BulletLab UI.

Provides a compact single-line input, plus an expandable floating window
with a multiline editor and a resizable output area. Commands are executed
via exec() in a configurable namespace, making robot objects and sim directly
accessible.

Example::

    from bulletlab.ui.panels.console import ConsolePanel

    console = ConsolePanel(namespace={"sim": sim, "robot": robot})
    console.render()
"""

from __future__ import annotations

import io
import traceback
from collections import deque
from contextlib import redirect_stderr, redirect_stdout
from typing import Any

try:
    import imgui

    _HAS_IMGUI = True
except ImportError:  # pragma: no cover
    imgui = None  # type: ignore[assignment]
    _HAS_IMGUI = False


class ConsolePanel:
    """Interactive Python console panel.

    Executes commands via ``exec()`` in a provided namespace, with output
    captured and displayed in a scrollable log.

    Args:
        namespace: Dictionary of variables available in the console namespace.
            Typically includes ``sim``, ``robot``, ``telemetry``, etc.
        max_history: Maximum number of output lines to retain.

    Example::

        console = ConsolePanel(namespace={"sim": sim, "robot": robot})
        console.execute("robot.links['wheel'].mass = 5")
    """

    def __init__(
        self,
        namespace: dict[str, Any] | None = None,
        max_history: int = 200,
    ) -> None:
        self._namespace: dict[str, Any] = namespace if namespace is not None else {}
        self._history: deque[str] = deque(maxlen=max_history)
        self._input_buf: list[str] = [""]  # mutable for imgui input
        self._cmd_history: list[str] = []
        self._cmd_index: int = -1
        self._scroll_to_bottom: bool = False
        self._focus_input: bool = True
        self._expanded: bool = False
        self._expanded_output_height: float = 260.0

        # Add some helpful builtins
        import builtins
        self._namespace.setdefault("__builtins__", builtins)

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    def update_namespace(self, updates: dict[str, Any]) -> None:
        """Update the console execution namespace.

        Args:
            updates: Key-value pairs to add or overwrite.

        Example::

            console.update_namespace({"robot": new_robot})
        """
        self._namespace.update(updates)

    def execute(self, command: str) -> None:
        """Execute a Python command string in the console namespace.

        Appends both the command and the result/error to the output log.

        Args:
            command: Python source code to execute.

        Example::

            console.execute("robot.links['wheel'].mass = 10")
        """
        command = command.strip()
        if not command:
            return

        self._history.append(f">>> {command}")
        self._cmd_history.append(command)
        self._cmd_index = -1

        captured = io.StringIO()
        result: Any = None
        error_lines: list[str] = []
        with redirect_stdout(captured), redirect_stderr(captured):
            try:
                # Compile as an expression first so values can be displayed.
                try:
                    expression = compile(command, "<console>", "eval")
                except SyntaxError:
                    expression = None

                if expression is not None:
                    result = eval(expression, self._namespace)  # noqa: S307
                else:
                    # Using the namespace for globals and locals makes
                    # assignments available to later console commands.
                    statement = compile(command, "<console>", "exec")
                    exec(statement, self._namespace, self._namespace)  # noqa: S102
            except Exception:
                error_lines = traceback.format_exc().splitlines()

        for line in captured.getvalue().splitlines():
            self._history.append(f"    {line}")
        if result is not None:
            self._history.append(f"    {result!r}")
        for line in error_lines:
            self._history.append(f"  {line}")

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

        _, new_text = imgui.input_text_multiline(
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

        for line in self._history:
            if line.startswith(">>>"):
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
            256,
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
        # Focus must be requested immediately before an input widget, so defer
        # restoration until the next frame after either submission route.
        self._focus_input = True

    def __repr__(self) -> str:
        return f"ConsolePanel(history={len(self._history)} lines)"
