"""
World – helper for populating a BulletLab simulation with environment objects.

The World class provides convenient methods for loading static environment
geometry (ground planes, terrain, obstacles) into the simulation.

Example::

    from bulletlab import Simulation
    from bulletlab.core.world import World

    sim = Simulation().start()
    world = World(sim)
    world.load_plane()
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pybullet as p
import pybullet_data

from bulletlab.core.simulation import Simulation


class World:
    """Helper for populating the simulation environment with static geometry.

    Args:
        sim: The :class:`~bulletlab.core.simulation.Simulation` instance to use.

    Example::

        sim = Simulation().start()
        world = World(sim)
        world.load_plane()
        world.load_urdf("box.urdf", position=(2, 0, 0.5))
    """

    def __init__(self, sim: Simulation) -> None:
        self._sim = sim
        self._bodies: list[int] = []

    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------

    def load_plane(
        self,
        texture_scale: float = 1.0,
    ) -> int:
        """Load the standard flat ground plane.

        Uses the ``plane.urdf`` asset bundled with pybullet_data.

        Args:
            texture_scale: Not used currently; reserved for future texture
                scaling support.

        Returns:
            PyBullet body ID of the plane.

        Example::

            world.load_plane()
        """
        body_id = p.loadURDF(
            "plane.urdf",
            physicsClientId=self._sim.client_id,
        )
        self._bodies.append(body_id)
        return body_id

    def load_urdf(
        self,
        path: str | Path,
        position: tuple[float, float, float] = (0.0, 0.0, 0.0),
        orientation: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
        fixed: bool = True,
        scale: float = 1.0,
    ) -> int:
        """Load an arbitrary URDF as a static or dynamic object.

        Args:
            path: Path to the URDF file. Can be an absolute path or a
                filename resolvable from the pybullet_data search path.
            position: Initial position ``(x, y, z)`` in meters.
            orientation: Initial orientation as a quaternion ``(x, y, z, w)``.
            fixed: If ``True``, the base link is fixed to the world frame.
            scale: Global scale factor for the loaded model.

        Returns:
            PyBullet body ID.

        Example::

            box_id = world.load_urdf("cube_small.urdf", position=(1, 0, 0.5))
        """
        flags = p.URDF_USE_INERTIA_FROM_FILE
        body_id = p.loadURDF(
            str(path),
            basePosition=list(position),
            baseOrientation=list(orientation),
            useFixedBase=fixed,
            globalScaling=scale,
            flags=flags,
            physicsClientId=self._sim.client_id,
        )
        self._bodies.append(body_id)
        return body_id

    def load_sdf(
        self,
        path: str | Path,
    ) -> list[int]:
        """Load an SDF file and return all resulting body IDs.

        Args:
            path: Path to the SDF file.

        Returns:
            List of PyBullet body IDs created.
        """
        ids = p.loadSDF(str(path), physicsClientId=self._sim.client_id)
        self._bodies.extend(ids)
        return list(ids)

    # ------------------------------------------------------------------
    # Convenience factories
    # ------------------------------------------------------------------

    def set_gravity(self, gx: float = 0.0, gy: float = 0.0, gz: float = -9.81) -> None:
        """Set simulation gravity.

        Convenience shorthand for :attr:`Simulation.gravity`.

        Args:
            gx: X component in m/s².
            gy: Y component in m/s².
            gz: Z component in m/s².

        Example::

            world.set_gravity(gz=-1.62)   # Moon
        """
        self._sim.gravity = (gx, gy, gz)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Remove all objects loaded by this World instance.

        Does not reset the entire simulation — only removes objects
        that this :class:`World` instance created.
        """
        for body_id in self._bodies:
            try:
                p.removeBody(body_id, physicsClientId=self._sim.client_id)
            except Exception:
                pass
        self._bodies.clear()

    @property
    def body_ids(self) -> list[int]:
        """List of all PyBullet body IDs managed by this World."""
        return list(self._bodies)

    def __repr__(self) -> str:
        return f"World(bodies={len(self._bodies)})"
