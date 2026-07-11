"""
Console execution engine. Handles the construction of the execution namespace
and background script execution.
"""

from __future__ import annotations

import queue
import sys
import threading
import time
import traceback
from typing import Any, Callable

from bulletlab.console.registry import registry
from bulletlab.console.context import _active_context


class ProxyObject:
    """A dynamic object used to populate the execution namespace with nested commands.
    If the command is 'sim.start', a ProxyObject is created for 'sim', and its
    'start' attribute is set to the registered function.
    """
    pass


class ConsoleEngine:
    """Sequential multi-statement script executor and namespace manager.

    Executes a script in a background thread, using a thread-local queue
    to push UI updates (output/errors) back to the main thread's simulation loop.
    This also dynamically builds proxy objects for registered commands so they
    can be called via dot-notation (e.g., sim.start()).
    """

    def __init__(
        self,
        sim: Any,
        on_output: Callable[[str], None],
        on_error: Callable[[str], None],
        on_echo: Callable[[str], None],
        on_done: Callable[[], None],
    ) -> None:
        self._sim = sim
        self._on_output = on_output
        self._on_error = on_error
        self._on_echo = on_echo
        self._on_done = on_done

        # Update global context
        _active_context.sim = sim
        _active_context.engine = self

        self._namespace: dict[str, Any] = {}
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._msg_queue: queue.Queue = queue.Queue()
        self._active: bool = False
        self._run_id: int = 0
        
        self.rebuild_namespace()

    @property
    def namespace(self) -> dict[str, Any]:
        return self._namespace
        
    def rebuild_namespace(self) -> None:
        """Rebuilds the execution namespace from the global registry."""
        import builtins
        
        # Start fresh
        self._namespace.clear()
        self._namespace["__builtins__"] = builtins
        
        # Populate from registry
        for name, meta in registry.get_all().items():
            parts = name.split('.')
            
            if len(parts) == 1:
                # Top level command (e.g., wait, load, gravity)
                self._namespace[name] = meta.func
            else:
                # Nested command (e.g., sim.start)
                current_level = self._namespace
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:
                        # Final part is the function
                        setattr(current_level, part, meta.func)
                    else:
                        # Intermediate part is a ProxyObject
                        if part not in current_level:
                            current_level[part] = ProxyObject()
                        current_level = current_level[part]

    def execute(self, command: str) -> None:
        """Execute a Python command string.
        
        Single-statement commands (including expressions) are executed
        immediately (REPL style). Multi-statement scripts are handed to
        the sequential runner for frame-by-frame execution.
        """
        import ast
        command = command.strip()
        if not command:
            return

        # If a script is already running, cancel it first
        if self._active:
            self.cancel()
            self._on_echo("# [Script cancelled — new submission]")

        try:
            tree = ast.parse(command, filename="<console>", mode="exec")
        except SyntaxError as exc:
            self._on_echo(f">>> {command}")
            self._on_error(f"  SyntaxError: {exc}")
            return

        is_multi = len(tree.body) > 1
        if not is_multi and len(tree.body) == 1:
            node = tree.body[0]
            if isinstance(
                node, 
                (ast.For, ast.While, ast.If, ast.With, ast.FunctionDef, ast.ClassDef, ast.Try)
            ):
                is_multi = True

        if is_multi:
            self.load(command)
        else:
            self._on_echo(f">>> {command}")
            self._exec_single(command)

    def _exec_single(self, command: str) -> None:
        """Execute a single statement/expression immediately (REPL style)."""
        import io
        from contextlib import redirect_stdout, redirect_stderr
        from bulletlab.console.exceptions import ConsoleError
        
        captured = io.StringIO()
        result: Any = None
        error_lines: list[str] = []
        
        with redirect_stdout(captured), redirect_stderr(captured):
            try:
                try:
                    expression = compile(command, "<console>", "eval")
                except SyntaxError:
                    expression = None

                if expression is not None:
                    result = eval(expression, self._namespace)  # noqa: S307
                else:
                    statement = compile(command, "<console>", "exec")
                    exec(statement, self._namespace, self._namespace)  # noqa: S102
            except ConsoleError as e:
                # Custom console errors get clean printing without tracebacks
                error_lines = [f"Error: {e}"]
            except Exception:
                error_lines = traceback.format_exc().splitlines()

        for line in captured.getvalue().splitlines():
            self._on_output(f"    {line}")
            
        if result is not None:
            self._on_output(f"    {result!r}")
            
        for line in error_lines:
            self._on_error(f"  {line}")

    @property
    def is_active(self) -> bool:
        """True while a script is being executed in the background."""
        return self._active

    def load(self, source: str) -> bool:
        """Spawn a background thread to execute the given source."""
        self.cancel()
        source = source.strip()
        if not source:
            return False

        try:
            compile(source, "<console>", "exec")
        except SyntaxError as exc:
            self._on_error(f"  SyntaxError: {exc}")
            return False

        self._active = True
        self._stop_event.clear()
        self._run_id += 1

        lines = source.splitlines()
        if len(lines) == 1:
            self._on_echo(f">>> {lines[0]}")
        else:
            self._on_echo(f">>> {lines[0]}\n" + "\n".join(lines[1:]))

        self._thread = threading.Thread(
            target=self._worker, args=(source, self._run_id), daemon=True
        )
        self._thread.start()
        return True

    def cancel(self) -> None:
        """Abort the current script immediately."""
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
        self._active = False

    def tick(self) -> None:
        """Process pending output and step commands from the script thread."""
        while not self._msg_queue.empty():
            run_id, msg_type, content = self._msg_queue.get()
            if run_id != self._run_id:
                continue
            
            if msg_type == "output":
                self._on_output(content)
            elif msg_type == "error":
                self._on_error(content)
            elif msg_type == "done":
                self._active = False
                self._on_done()
            elif msg_type == "step":
                n, ack_event = content
                if self._sim is not None:
                    for _ in range(n):
                        self._sim.step()
                ack_event.set()

    def _worker(self, source: str, run_id: int) -> None:
        """Background thread worker for script execution."""
        thread_id = threading.get_ident()

        def tracer(frame: Any, event: str, arg: Any) -> Callable:
            if self._stop_event.is_set():
                raise SystemExit("Script cancelled")
            return tracer

        sys.settrace(tracer)

        class CaptureWriter:
            def __init__(self, q: queue.Queue, prefix: str, run_id: int) -> None:
                self.q = q
                self.prefix = prefix
                self.run_id = run_id
                self.buf = ""

            def write(self, s: str) -> None:
                if threading.get_ident() != thread_id:
                    return
                self.buf += s
                if "\n" in self.buf:
                    lines = self.buf.split("\n")
                    for line in lines[:-1]:
                        msg_type = "output" if self.prefix == "    " else "error"
                        self.q.put((self.run_id, msg_type, self.prefix + line))
                    self.buf = lines[-1]

            def flush(self) -> None:
                pass

        out_capture = CaptureWriter(self._msg_queue, "    ", run_id)
        err_capture = CaptureWriter(self._msg_queue, "  ", run_id)

        orig_stdout = sys.stdout
        orig_stderr = sys.stderr

        class RouterOut:
            def write(self, s: str) -> None:
                if threading.get_ident() == thread_id:
                    out_capture.write(s)
                else:
                    orig_stdout.write(s)

            def flush(self) -> None:
                if threading.get_ident() != thread_id:
                    orig_stdout.flush()

        class RouterErr:
            def write(self, s: str) -> None:
                if threading.get_ident() == thread_id:
                    err_capture.write(s)
                else:
                    orig_stderr.write(s)

            def flush(self) -> None:
                if threading.get_ident() != thread_id:
                    orig_stderr.flush()

        sys.stdout = RouterOut()  # type: ignore
        sys.stderr = RouterErr()  # type: ignore

        try:
            code = compile(source, "<console>", "exec")
            exec(code, self._namespace, self._namespace)  # noqa: S102
        except SystemExit:
            pass
        except Exception:
            for line in traceback.format_exc().splitlines():
                self._msg_queue.put((run_id, "error", f"  {line}"))
        finally:
            sys.settrace(None)

            if out_capture.buf:
                self._msg_queue.put((run_id, "output", out_capture.prefix + out_capture.buf))
            if err_capture.buf:
                self._msg_queue.put((run_id, "error", err_capture.prefix + err_capture.buf))

            sys.stdout = orig_stdout
            sys.stderr = orig_stderr
            self._msg_queue.put((run_id, "done", None))
