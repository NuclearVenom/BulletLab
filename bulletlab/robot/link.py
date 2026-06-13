"""
Link – a rigid body segment in a robot model.

The Link class wraps a single PyBullet link and exposes its physical
properties (mass, friction, restitution, damping) as Python attributes.
Setting any property automatically calls PyBullet's changeDynamics.

Example::

    link = robot.links["wheel_fl"]
    link.mass = 2.5
    link.friction = 0.8
    link.restitution = 0.1
    print(link.position)          # world position
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pybullet as p

if TYPE_CHECKING:
    from bulletlab.core.simulation import Simulation


class Link:
    """A single rigid body link in a robot model.

    Links are typically not instantiated directly — they are created by
    :class:`~bulletlab.robot.robot.Robot` when loading a URDF/MJCF file.
    Access them via ``robot.links["link_name"]``.

    The base link (index -1 in PyBullet) is also exposed as ``robot.links``
    under its name.

    Args:
        name: Link name (from URDF).
        index: PyBullet link index (``-1`` for base link).
        body_id: PyBullet body ID of the parent robot.
        sim: The :class:`~bulletlab.core.simulation.Simulation` instance.

    Example::

        link = robot.links["chassis"]
        link.mass = 10.0
        link.friction = 0.8
        print(link.position)
    """

    def __init__(
        self,
        name: str,
        index: int,
        body_id: int,
        sim: "Simulation",
    ) -> None:
        self._name = name
        self._index = index
        self._body_id = body_id
        self._sim = sim
        # Cache damping values: PyBullet's getDynamicsInfo returns 0.0 for the
        # base link (index -1) even after changeDynamics is called, so we track
        # the last written value ourselves.
        self._linear_damping_cache: float | None = None
        self._angular_damping_cache: float | None = None

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Link name as defined in the URDF."""
        return self._name

    @property
    def index(self) -> int:
        """PyBullet link index (``-1`` for base link)."""
        return self._index

    # ------------------------------------------------------------------
    # Physical properties (get/set → changeDynamics)
    # ------------------------------------------------------------------

    @property
    def mass(self) -> float:
        """Link mass in kilograms.

        Setting this value calls ``pybullet.changeDynamics`` immediately.

        Example::

            robot.links["chassis"].mass = 5.0
        """
        info = p.getDynamicsInfo(
            self._body_id,
            self._index,
            physicsClientId=self._sim.client_id,
        )
        return float(info[0])

    @mass.setter
    def mass(self, value: float) -> None:
        p.changeDynamics(
            self._body_id,
            self._index,
            mass=float(value),
            physicsClientId=self._sim.client_id,
        )

    @property
    def friction(self) -> float:
        """Lateral friction coefficient.

        Setting this value calls ``pybullet.changeDynamics`` immediately.

        Example::

            robot.links["wheel_fl"].friction = 1.2
        """
        info = p.getDynamicsInfo(
            self._body_id,
            self._index,
            physicsClientId=self._sim.client_id,
        )
        return float(info[1])

    @friction.setter
    def friction(self, value: float) -> None:
        p.changeDynamics(
            self._body_id,
            self._index,
            lateralFriction=float(value),
            physicsClientId=self._sim.client_id,
        )

    @property
    def restitution(self) -> float:
        """Coefficient of restitution (bounciness), in range [0, 1].

        Setting this value calls ``pybullet.changeDynamics`` immediately.

        Example::

            robot.links["bumper"].restitution = 0.5
        """
        info = p.getDynamicsInfo(
            self._body_id,
            self._index,
            physicsClientId=self._sim.client_id,
        )
        return float(info[5])

    @restitution.setter
    def restitution(self, value: float) -> None:
        p.changeDynamics(
            self._body_id,
            self._index,
            restitution=float(value),
            physicsClientId=self._sim.client_id,
        )

    @property
    def linear_damping(self) -> float:
        """Linear velocity damping coefficient.

        Setting this value calls ``pybullet.changeDynamics`` immediately.

        Example::

            robot.links["chassis"].linear_damping = 0.1
        """
        if self._linear_damping_cache is not None:
            return self._linear_damping_cache
        info = p.getDynamicsInfo(
            self._body_id,
            self._index,
            physicsClientId=self._sim.client_id,
        )
        return float(info[6])

    @linear_damping.setter
    def linear_damping(self, value: float) -> None:
        self._linear_damping_cache = float(value)
        p.changeDynamics(
            self._body_id,
            self._index,
            linearDamping=float(value),
            physicsClientId=self._sim.client_id,
        )

    @property
    def angular_damping(self) -> float:
        """Angular velocity damping coefficient.

        Setting this value calls ``pybullet.changeDynamics`` immediately.

        Example::

            robot.links["chassis"].angular_damping = 0.1
        """
        if self._angular_damping_cache is not None:
            return self._angular_damping_cache
        info = p.getDynamicsInfo(
            self._body_id,
            self._index,
            physicsClientId=self._sim.client_id,
        )
        return float(info[7])

    @angular_damping.setter
    def angular_damping(self, value: float) -> None:
        self._angular_damping_cache = float(value)
        p.changeDynamics(
            self._body_id,
            self._index,
            angularDamping=float(value),
            physicsClientId=self._sim.client_id,
        )

    @property
    def damping(self) -> float:
        """Combined linear damping (shorthand for :attr:`linear_damping`).

        Setting this updates both linear and angular damping symmetrically.

        Example::

            robot.links["chassis"].damping = 0.05
        """
        return self.linear_damping

    @damping.setter
    def damping(self, value: float) -> None:
        self._linear_damping_cache = float(value)
        self._angular_damping_cache = float(value)
        p.changeDynamics(
            self._body_id,
            self._index,
            linearDamping=float(value),
            angularDamping=float(value),
            physicsClientId=self._sim.client_id,
        )

    @property
    def spinning_friction(self) -> float:
        """Spinning friction coefficient.

        Example::

            robot.links["wheel"].spinning_friction = 0.01
        """
        info = p.getDynamicsInfo(
            self._body_id,
            self._index,
            physicsClientId=self._sim.client_id,
        )
        return float(info[2])

    @spinning_friction.setter
    def spinning_friction(self, value: float) -> None:
        p.changeDynamics(
            self._body_id,
            self._index,
            spinningFriction=float(value),
            physicsClientId=self._sim.client_id,
        )

    @property
    def rolling_friction(self) -> float:
        """Rolling friction coefficient.

        Example::

            robot.links["wheel"].rolling_friction = 0.01
        """
        info = p.getDynamicsInfo(
            self._body_id,
            self._index,
            physicsClientId=self._sim.client_id,
        )
        return float(info[3])

    @rolling_friction.setter
    def rolling_friction(self, value: float) -> None:
        p.changeDynamics(
            self._body_id,
            self._index,
            rollingFriction=float(value),
            physicsClientId=self._sim.client_id,
        )

    # ------------------------------------------------------------------
    # State reads (world-frame)
    # ------------------------------------------------------------------

    @property
    def position(self) -> tuple[float, float, float]:
        """World-frame position of this link's COM in meters ``(x, y, z)``.

        For the base link (index -1), queries the base position directly.

        Example::

            x, y, z = robot.links["chassis"].position
        """
        if self._index == -1:
            pos, _ = p.getBasePositionAndOrientation(
                self._body_id,
                physicsClientId=self._sim.client_id,
            )
            return tuple(float(v) for v in pos)  # type: ignore[return-value]
        state = p.getLinkState(
            self._body_id,
            self._index,
            physicsClientId=self._sim.client_id,
        )
        return tuple(float(v) for v in state[0])  # type: ignore[return-value]

    @property
    def orientation(self) -> tuple[float, float, float, float]:
        """World-frame orientation as a quaternion ``(x, y, z, w)``.

        Example::

            q = robot.links["chassis"].orientation
        """
        if self._index == -1:
            _, orn = p.getBasePositionAndOrientation(
                self._body_id,
                physicsClientId=self._sim.client_id,
            )
            return tuple(float(v) for v in orn)  # type: ignore[return-value]
        state = p.getLinkState(
            self._body_id,
            self._index,
            physicsClientId=self._sim.client_id,
        )
        return tuple(float(v) for v in state[1])  # type: ignore[return-value]

    @property
    def velocity(self) -> tuple[float, float, float]:
        """World-frame linear velocity of this link in m/s ``(vx, vy, vz)``.

        Example::

            vx, vy, vz = robot.links["chassis"].velocity
        """
        if self._index == -1:
            vel, _ = p.getBaseVelocity(
                self._body_id,
                physicsClientId=self._sim.client_id,
            )
            return tuple(float(v) for v in vel)  # type: ignore[return-value]
        state = p.getLinkState(
            self._body_id,
            self._index,
            computeLinkVelocity=1,
            physicsClientId=self._sim.client_id,
        )
        return tuple(float(v) for v in state[6])  # type: ignore[return-value]

    @property
    def angular_velocity(self) -> tuple[float, float, float]:
        """World-frame angular velocity of this link in rad/s ``(wx, wy, wz)``.

        Example::

            wx, wy, wz = robot.links["chassis"].angular_velocity
        """
        if self._index == -1:
            _, avel = p.getBaseVelocity(
                self._body_id,
                physicsClientId=self._sim.client_id,
            )
            return tuple(float(v) for v in avel)  # type: ignore[return-value]
        state = p.getLinkState(
            self._body_id,
            self._index,
            computeLinkVelocity=1,
            physicsClientId=self._sim.client_id,
        )
        return tuple(float(v) for v in state[7])  # type: ignore[return-value]

    @property
    def inertia(self) -> tuple[float, float, float]:
        """Inertia diagonal ``(Ixx, Iyy, Izz)`` in kg·m²."""
        info = p.getDynamicsInfo(
            self._body_id,
            self._index,
            physicsClientId=self._sim.client_id,
        )
        return tuple(float(v) for v in info[2])  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"Link({self._name!r}, index={self._index}, mass={self.mass:.3f}kg)"
