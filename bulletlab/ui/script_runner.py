"""
ScriptRunner – line-by-line sequential console script executor for BulletLab.

Executes a multi-statement Python script one top-level statement at a time,
yielding control back to the simulation loop between statements. This makes
sequential robot commands visible — each position change, velocity command,
or loop iteration produces a rendered physics frame before the next line runs.

Special built-in commands injected into the execution namespace:

    wait(ms: int | float)
        Pause execution for the given number of milliseconds before the next
        statement runs. The simulation and UI continue stepping normally
        during the wait. Example:

            robot.joints['arm'].position = 1.0
            wait(500)   # hold for 500 ms, then continue
            robot.joints['arm'].position = 0.0

    step(n: int = 1)
        Advance the simulation by ``n`` physics steps immediately (within the
        current frame) then continue. Useful when the next statement depends
        on physics having settled. Example:

            robot.joints['arm'].position = 1.0
            step(240)   # let 1 simulated second pass
            print(robot.joints['arm'].position)

Architecture
------------
    1. The submitted source is parsed into an AST.
    2. Top-level statements are extracted as a list of single-statement
       code objects.
    3. Each call to ``tick()`` executes the next pending statement.
    4. If the statement called ``wait(ms)``, ticking is suspended until
       the wall-clock deadline has passed.
    5. Output and exceptions are captured and posted back to the caller
       via a callback (used by ConsolePanel to append to the history log).
"""

from __future__ import annotations

import queue
import sys
import threading
import time
import traceback
from typing import Any, Callable


class ScriptRunner:
    """Sequential multi-statement script executor.

    Executes a script in a background thread, using a thread-local queue
    to push UI updates (output/errors) back to the main thread's simulation loop.
    This allows constructs like `for` loops to run naturally, while `wait()`
    and `step()` functions communicate cleanly with the UI.

    Args:
        namespace: The execution namespace (shared with ConsolePanel).
        sim: The Simulation instance, used for inline ``step(n)`` calls.
        on_output: Callback invoked with each captured output line.
        on_error: Callback invoked with each error/traceback line.
        on_echo: Callback invoked to echo the ``>>> statement`` prefix.
        on_done: Callback invoked when the script finishes or is cancelled.
    """

    def __init__(
        self,
        namespace: dict[str, Any],
        sim: Any,
        on_output: Callable[[str], None],
        on_error: Callable[[str], None],
        on_echo: Callable[[str], None],
        on_done: Callable[[], None],
    ) -> None:
        self._namespace = namespace
        self._sim = sim
        self._on_output = on_output
        self._on_error = on_error
        self._on_echo = on_echo
        self._on_done = on_done

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._msg_queue: queue.Queue = queue.Queue()
        self._active: bool = False
        self._run_id: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        """True while a script is being executed in the background."""
        return self._active

    def load(self, source: str) -> bool:
        """Spawn a background thread to execute the given source.

        Returns True if the source parsed successfully, False on syntax error.
        The previous script (if any) is cancelled first.
        """
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
        # Fresh event per run: the old thread keeps its reference to the old
        # event (which stays set), preventing it from continuing after cancel.
        self._stop_event = threading.Event()
        self._run_id += 1
        run_stop_event = self._stop_event

        lines = source.splitlines()
        if len(lines) == 1:
            self._on_echo(f">>> {lines[0]}")
        else:
            cont = "\n".join(f"... {l}" for l in lines[1:])
            self._on_echo(f">>> {lines[0]}\n{cont}")

        self._thread = threading.Thread(
            target=self._worker, args=(source, self._run_id, run_stop_event), daemon=True
        )
        self._thread.start()
        return True

    def cancel(self) -> None:
        """Abort the current script immediately."""
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
        self._active = False

    def tick(self) -> None:
        """Process pending output and step commands from the script thread.

        Call this once per simulation/UI frame.
        """
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

    # ------------------------------------------------------------------
    # Internal worker
    # ------------------------------------------------------------------

    def _worker(self, source: str, run_id: int, stop_event: threading.Event) -> None:
        """Background thread worker for script execution."""
        thread_id = threading.get_ident()

        # Thread-local trace function allows near-instant cancellation 
        # even if the script is in an infinite loop.
        def tracer(frame: Any, event: str, arg: Any) -> Callable:
            if stop_event.is_set():
                raise SystemExit("Script cancelled")
            return tracer

        sys.settrace(tracer)

        # Route ONLY this thread's stdout/stderr to the message queue
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
            # Silently exit; the UI will print '# [Script cancelled]'
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

    # ------------------------------------------------------------------
    # Namespace helpers
    # ------------------------------------------------------------------

    def make_builtins(self) -> dict[str, Any]:
        """Return the special built-in commands to inject into the namespace."""
        
        def wait(ms: int | float = 0) -> None:
            """Pause script execution for *ms* milliseconds."""
            end_time = time.monotonic() + (ms / 1000.0)
            while time.monotonic() < end_time:
                if self._stop_event.is_set():
                    raise SystemExit("Script cancelled")
                time.sleep(0.01)

        def step(n: int = 1) -> None:
            """Advance the simulation by *n* physics steps."""
            n = max(1, int(n))
            ack_event = threading.Event()
            self._msg_queue.put((self._run_id, "step", (n, ack_event)))
            while not ack_event.is_set():
                if self._stop_event.is_set():
                    raise SystemExit("Script cancelled")
                ack_event.wait(timeout=0.01)

        return {"wait": wait, "step": step}
