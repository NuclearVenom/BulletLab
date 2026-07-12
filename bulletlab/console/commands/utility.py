"""
Utility console commands like wait and step.
"""

import time
import threading

from bulletlab.console.decorators import command
from bulletlab.console.context import get_context
from bulletlab.console.exceptions import CommandError


def _get_stop_event():
    """Return the stop event for the current script thread.
    
    Uses the thread-local set by the engine's _worker so that wait()/step()
    always check the correct per-run event, even after engine._stop_event has
    been replaced by a newer load() call.
    """
    from bulletlab.console.engine import get_current_stop_event
    stop = get_current_stop_event()
    if stop is not None:
        return stop
    # Fallback: try the engine's current event (non-threaded use or tests)
    ctx = get_context()
    engine = ctx.engine
    if engine is not None:
        return engine._stop_event
    return None


@command(
    name="wait",
    description="Pause script execution for a specified number of milliseconds.",
    category="Utility"
)
def wait(ms: int | float = 0) -> None:
    """Pause script execution for *ms* milliseconds."""
    if not isinstance(ms, (int, float)):
        raise CommandError("wait() requires a numeric argument (milliseconds).")

    stop_event = _get_stop_event()
    end_time = time.monotonic() + (ms / 1000.0)
    while time.monotonic() < end_time:
        if stop_event is not None and stop_event.is_set():
            raise SystemExit("Script cancelled")
        time.sleep(0.01)


@command(
    name="step",
    description="Advance the simulation by the specified number of physics steps.",
    category="Utility"
)
def step(n: int = 1) -> None:
    """Advance the simulation by *n* physics steps."""
    ctx = get_context()
    engine = ctx.engine

    if not isinstance(n, int):
        raise CommandError("step() requires an integer argument.")

    n = max(1, int(n))
    ack_event = threading.Event()
    stop_event = _get_stop_event()

    if engine:
        engine._msg_queue.put((engine._run_id, "step", (n, ack_event)))
        while not ack_event.is_set():
            if stop_event is not None and stop_event.is_set():
                raise SystemExit("Script cancelled")
            ack_event.wait(timeout=0.01)
