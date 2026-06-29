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
    world.create_box((0.5, 0.5, 0.5), position=(2, 0, 0.25), color=(0.6, 0.3, 0.1, 1))
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Optional, Sequence

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
        world.create_box((0.3, 0.3, 0.3), position=(1, 0, 0.15))
    """

    def __init__(self, sim: Simulation) -> None:
        self._sim = sim
        self._bodies: list[int] = []

    # ------------------------------------------------------------------
    # URDF / SDF loaders
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
    # Primitive shape factories
    # ------------------------------------------------------------------

    def create_box(
        self,
        size: tuple[float, float, float] = (0.5, 0.5, 0.5),
        position: tuple[float, float, float] = (0.0, 0.0, 0.5),
        orientation: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
        mass: float = 0.0,
        color: tuple[float, float, float, float] = (0.6, 0.6, 0.6, 1.0),
    ) -> int:
        """Create a box-shaped body.

        Args:
            size: Full extents ``(width, depth, height)`` in meters.
                Half-extents are computed internally.
            position: World position ``(x, y, z)`` of the centre.
            orientation: Quaternion ``(x, y, z, w)``.
            mass: Mass in kg.  ``0`` makes it a static obstacle.
            color: RGBA color tuple, each component in ``[0, 1]``.

        Returns:
            PyBullet body ID.

        Example::

            world.create_box((1.0, 0.5, 0.3), position=(2, 0, 0.15), color=(0.8, 0.4, 0.1, 1))
        """
        cid = self._sim.client_id
        half = [s / 2.0 for s in size]
        col = p.createCollisionShape(p.GEOM_BOX, halfExtents=half, physicsClientId=cid)
        vis = p.createVisualShape(
            p.GEOM_BOX, halfExtents=half, rgbaColor=list(color), physicsClientId=cid
        )
        body_id = p.createMultiBody(
            baseMass=mass,
            baseCollisionShapeIndex=col,
            baseVisualShapeIndex=vis,
            basePosition=list(position),
            baseOrientation=list(orientation),
            physicsClientId=cid,
        )
        self._bodies.append(body_id)
        return body_id

    def create_sphere(
        self,
        radius: float = 0.25,
        position: tuple[float, float, float] = (0.0, 0.0, 0.25),
        mass: float = 0.0,
        color: tuple[float, float, float, float] = (0.5, 0.5, 0.8, 1.0),
    ) -> int:
        """Create a sphere-shaped body.

        Args:
            radius: Sphere radius in meters.
            position: World position ``(x, y, z)`` of the centre.
            mass: Mass in kg.  ``0`` = static.
            color: RGBA color tuple.

        Returns:
            PyBullet body ID.

        Example::

            world.create_sphere(radius=0.3, position=(0, 2, 0.3), color=(0.2, 0.8, 0.2, 1))
        """
        cid = self._sim.client_id
        col = p.createCollisionShape(p.GEOM_SPHERE, radius=radius, physicsClientId=cid)
        vis = p.createVisualShape(
            p.GEOM_SPHERE, radius=radius, rgbaColor=list(color), physicsClientId=cid
        )
        body_id = p.createMultiBody(
            baseMass=mass,
            baseCollisionShapeIndex=col,
            baseVisualShapeIndex=vis,
            basePosition=list(position),
            physicsClientId=cid,
        )
        self._bodies.append(body_id)
        return body_id

    def create_capsule(
        self,
        radius: float = 0.15,
        height: float = 0.6,
        position: tuple[float, float, float] = (0.0, 0.0, 0.5),
        mass: float = 0.0,
        color: tuple[float, float, float, float] = (0.7, 0.5, 0.3, 1.0),
    ) -> int:
        """Create a capsule-shaped body (cylinder with hemispherical caps).

        Args:
            radius: Capsule radius in meters.
            height: Height of the cylindrical section (not counting caps).
            position: World position ``(x, y, z)`` of the centre.
            mass: Mass in kg.  ``0`` = static.
            color: RGBA color tuple.

        Returns:
            PyBullet body ID.

        Example::

            world.create_capsule(radius=0.1, height=0.8, position=(1, 1, 0.5))
        """
        cid = self._sim.client_id
        col = p.createCollisionShape(
            p.GEOM_CAPSULE, radius=radius, height=height, physicsClientId=cid
        )
        vis = p.createVisualShape(
            p.GEOM_CAPSULE,
            radius=radius,
            length=height,
            rgbaColor=list(color),
            physicsClientId=cid,
        )
        body_id = p.createMultiBody(
            baseMass=mass,
            baseCollisionShapeIndex=col,
            baseVisualShapeIndex=vis,
            basePosition=list(position),
            physicsClientId=cid,
        )
        self._bodies.append(body_id)
        return body_id

    # ------------------------------------------------------------------
    # Terrain
    # ------------------------------------------------------------------

    def load_heightfield(
        self,
        heights: "Sequence[float] | list[list[float]]",
        rows: int | None = None,
        cols: int | None = None,
        xy_scale: float = 0.1,
        z_scale: float = 0.25,
        position: tuple[float, float, float] = (0.0, 0.0, 0.0),
        color: tuple[float, float, float, float] = (0.55, 0.45, 0.35, 1.0),
    ) -> int:
        """Build a heightfield terrain from a flat list or a 2-D array.

        The heightfield is created as a static (mass = 0) body.

        Args:
            heights: Height values.  Can be:

                * A flat ``list[float]`` of length ``rows * cols``.
                * A 2-D list / numpy array of shape ``(rows, cols)``; will be
                  flattened automatically.

            rows: Number of rows in the heightfield grid.  Required when
                ``heights`` is already flat; inferred automatically for 2-D input.
            cols: Number of columns.  Same rules as ``rows``.
            xy_scale: Physical size of each grid cell in the X and Y
                directions (meters per cell).  Defaults to 0.1 m.
            z_scale: Vertical scale factor (meters per height-unit).
            position: World position of the terrain centre ``(x, y, z)``.
            color: RGBA dirt / terrain color.

        Returns:
            PyBullet body ID of the terrain.

        Example::

            import numpy as np, math
            n = 128
            xs = np.linspace(0, 4 * math.pi, n)
            H = np.outer(np.sin(xs), np.cos(xs))
            world.load_heightfield(H, xy_scale=0.05, z_scale=0.3)
        """
        import numpy as np  # optional dep — only needed here

        cid = self._sim.client_id

        # Normalise to flat list + determine grid size
        arr = np.asarray(heights, dtype=np.float64)
        if arr.ndim == 2:
            r, c = arr.shape
            flat = arr.flatten().tolist()
        elif arr.ndim == 1:
            if rows is None or cols is None:
                n = int(math.isqrt(len(arr)))
                r, c = n, n
                if r * c != len(arr):
                    raise ValueError(
                        "Cannot infer rows/cols from flat heights list — "
                        "please supply rows= and cols= explicitly."
                    )
            else:
                r, c = rows, cols
            flat = arr.tolist()
        else:
            raise ValueError("heights must be a 1-D or 2-D sequence.")

        col_shape = p.createCollisionShape(
            p.GEOM_HEIGHTFIELD,
            meshScale=[xy_scale, xy_scale, z_scale],
            heightfieldData=flat,
            numHeightfieldRows=r,
            numHeightfieldColumns=c,
            physicsClientId=cid,
        )
        body_id = p.createMultiBody(
            baseCollisionShapeIndex=col_shape,
            basePosition=list(position),
            physicsClientId=cid,
        )
        p.changeVisualShape(body_id, -1, rgbaColor=list(color), physicsClientId=cid)
        self._bodies.append(body_id)
        return body_id

    # ------------------------------------------------------------------
    # Batch obstacle generation
    # ------------------------------------------------------------------

    def scatter_obstacles(
        self,
        count: int = 20,
        kind: str = "box",
        size_range: tuple[float, float] = (0.2, 0.6),
        region: tuple[float, float, float, float] = (-10.0, -10.0, 10.0, 10.0),
        mass: float = 0.0,
        color: tuple[float, float, float, float] = (0.4, 0.4, 0.4, 1.0),
        seed: int | None = None,
    ) -> list[int]:
        """Randomly scatter obstacles across a rectangular region.

        Args:
            count: Number of obstacles to create.
            kind: Shape type — ``"box"``, ``"sphere"``, or ``"capsule"``.
            size_range: ``(min_size, max_size)`` — uniform random size drawn
                per obstacle.  For boxes this sets each half-extent; for
                spheres it sets the radius.
            region: ``(x_min, y_min, x_max, y_max)`` bounds for placement.
            mass: Mass per obstacle.  ``0`` = static.
            color: RGBA color applied to all obstacles.
            seed: Optional RNG seed for reproducibility.

        Returns:
            List of PyBullet body IDs created.

        Example::

            ids = world.scatter_obstacles(30, kind="box",
                                          size_range=(0.2, 0.5),
                                          region=(-8, -8, 8, 8),
                                          color=(0.4, 0.4, 0.4, 1))
        """
        rng = random.Random(seed)
        x_min, y_min, x_max, y_max = region
        ids: list[int] = []

        for _ in range(count):
            x = rng.uniform(x_min, x_max)
            y = rng.uniform(y_min, y_max)
            s = rng.uniform(*size_range)

            if kind == "box":
                sx = rng.uniform(*size_range)
                sy = rng.uniform(*size_range)
                sz = rng.uniform(*size_range)
                bid = self.create_box(
                    size=(sx, sy, sz),
                    position=(x, y, sz / 2),
                    mass=mass,
                    color=color,
                )
            elif kind == "sphere":
                bid = self.create_sphere(
                    radius=s,
                    position=(x, y, s),
                    mass=mass,
                    color=color,
                )
            elif kind == "capsule":
                h = rng.uniform(*size_range)
                bid = self.create_capsule(
                    radius=s / 2,
                    height=h,
                    position=(x, y, h / 2 + s / 2),
                    mass=mass,
                    color=color,
                )
            else:
                raise ValueError(f"Unknown obstacle kind: {kind!r}. Use 'box', 'sphere', or 'capsule'.")

            ids.append(bid)

        return ids

    # ------------------------------------------------------------------
    # Gravity
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

    def remove_body(self, body_id: int) -> None:
        """Remove a single body from the simulation.

        If the body was created by this World instance it is also removed from
        the internal tracking list so ``world.clear()`` stays consistent.

        Args:
            body_id: PyBullet body ID to remove.

        Example::

            rock = world.create_box(...)
            # ... later ...
            world.remove_body(rock)
        """
        try:
            p.removeBody(body_id, physicsClientId=self._sim.client_id)
        except Exception:
            pass
        if body_id in self._bodies:
            self._bodies.remove(body_id)

    def clear(self) -> None:
        """Remove all objects loaded by this World instance.

        Does not reset the entire simulation — only removes objects
        that this :class:`World` instance created.
        """
        for body_id in list(self._bodies):
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
