"""
SimTimer – a utility for tracking simulation time and wall-clock time.

Example::

    from bulletlab.utils.timer import SimTimer

    timer = SimTimer(timestep=1/240)
    for _ in range(1000):
        sim.step()
        timer.tick()
    print(f"Sim time: {timer.sim_time:.3f}s  Wall time: {timer.wall_time:.3f}s")
"""

from __future__ import annotations

import time


class SimTimer:
    """Tracks simulation step count, simulated time, and wall-clock time.

    Args:
        timestep: Simulation timestep in seconds (should match
            :attr:`Simulation.timestep`).

    Example::

        timer = SimTimer(timestep=1/240)
        timer.tick()                  # call each sim step
        print(timer.sim_time)         # time in seconds
        print(timer.wall_time)        # real-world elapsed seconds
        print(timer.step_count)       # total ticks
    """

    def __init__(self, timestep: float = 1.0 / 240.0) -> None:
        self._timestep = timestep
        self._step_count: int = 0
        self._start_time: float = time.monotonic()
        self._last_tick_time: float = self._start_time

    def tick(self) -> None:
        """Advance the timer by one simulation step.

        Call this once per call to :meth:`Simulation.step`.

        Example::

            timer.tick()
        """
        self._step_count += 1
        self._last_tick_time = time.monotonic()

    def reset(self) -> None:
        """Reset all counters to zero.

        Example::

            timer.reset()
        """
        self._step_count = 0
        self._start_time = time.monotonic()
        self._last_tick_time = self._start_time

    @property
    def step_count(self) -> int:
        """Total number of :meth:`tick` calls since creation or last :meth:`reset`."""
        return self._step_count

    @property
    def sim_time(self) -> float:
        """Simulated elapsed time in seconds (``step_count * timestep``)."""
        return self._step_count * self._timestep

    @property
    def wall_time(self) -> float:
        """Real-world elapsed time in seconds since creation or last :meth:`reset`."""
        return time.monotonic() - self._start_time

    @property
    def timestep(self) -> float:
        """The configured simulation timestep in seconds."""
        return self._timestep

    @timestep.setter
    def timestep(self, value: float) -> None:
        self._timestep = float(value)

    @property
    def real_time_factor(self) -> float:
        """Ratio of simulated time to wall-clock time.

        A value of 1.0 means the simulation runs in real-time.
        A value > 1.0 means the simulation is running faster than real-time.
        """
        wt = self.wall_time
        if wt == 0.0:
            return 0.0
        return self.sim_time / wt

    def __repr__(self) -> str:
        return (
            f"SimTimer(step={self._step_count}, "
            f"sim_t={self.sim_time:.3f}s, "
            f"wall_t={self.wall_time:.3f}s, "
            f"rtf={self.real_time_factor:.2f})"
        )
