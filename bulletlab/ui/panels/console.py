"""
ConsolePanel – interactive Python command console in the BulletLab UI.

Provides a single-line input field and a scrollable output log. Commands
are executed via exec() in a configurable namespace, making robot objects
and sim directly accessible.

Example::

    from bulletlab.ui.panels.console import ConsolePanel

    console = ConsolePanel(namespace={"sim": sim, "robot": robot})
    console.render()
"""

from __future__ import annotations

import traceback
from collections import deque
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

        try:
            # Try eval first (for expressions)
            try:
                result = eval(command, self._namespace)  # noqa: S307
                if result is not None:
                    self._history.append(f"    {result!r}")
            except SyntaxError:
                # Pass namespace as both globals AND locals so that
                # assignments (x = 42) are written back into the shared dict.
                exec(command, self._namespace, self._namespace)  # noqa: S102
        except Exception:
            for line in traceback.format_exc().splitlines():
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
        """Draw the console panel contents.

        Must be called inside an active ImGui window context.
        """
        if not _HAS_IMGUI:
            return

        # Output area (child window for scrolling)
        avail_height = imgui.get_content_region_available()[1] - 30
        imgui.begin_child(
            "console_output",
            width=0,
            height=max(avail_height, 50),
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

        # Input field
        imgui.push_item_width(-65)
        enter_pressed = False

        # We need to use input_text - imgui binding style
        input_flags = imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
        changed, new_text = imgui.input_text(
            "##console_input",
            self._input_buf[0],
            256,
            flags=input_flags,
        )
        self._input_buf[0] = new_text

        if changed:  # Enter was pressed
            enter_pressed = True

        imgui.pop_item_width()
        imgui.same_line()

        if imgui.button("Run##console_run") or enter_pressed:
            cmd = self._input_buf[0].strip()
            if cmd:
                self.execute(cmd)
                self._input_buf[0] = ""

    def __repr__(self) -> str:
        return f"ConsolePanel(history={len(self._history)} lines)"
