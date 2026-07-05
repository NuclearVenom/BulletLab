"""
Headless simulation smoke test for BulletLab CI.

Verifies that the core simulation stack — PyBullet DIRECT mode, World, and
Robot loading — executes correctly in a headless environment with no display,
no GUI, no network access, and no external assets beyond what pybullet_data
provides.

This test is deliberately minimal and deterministic. Its goal is to confirm
that the full simulation pipeline boots, performs physics, and produces valid
observable state. A failure here indicates a fundamental installation or
compatibility problem.
"""

from __future__ import annotations

import pytest
import pybullet_data

from bulletlab.core.simulation import Simulation
from bulletlab.core.world import World
from bulletlab.robot.robot import Robot
from bulletlab.utils.urdf_utils import find_urdf


class TestHeadlessSmoke:
    """Minimal headless simulation stack validation."""

    def test_direct_mode_connect_disconnect(self):
        """PyBullet DIRECT mode must connect and disconnect cleanly."""
        sim = Simulation(mode="direct")
        assert not sim.is_connected, "Should start disconnected"
        sim.start()
        assert sim.is_connected, "Should be connected after start()"
        sim.stop()
        assert not sim.is_connected, "Should be disconnected after stop()"

    def test_simulation_steps_in_direct_mode(self):
        """Simulation must advance step count in DIRECT mode."""
        sim = Simulation(mode="direct")
        sim.start()
        try:
            assert sim.step_count == 0
            for _ in range(10):
                sim.step()
            assert sim.step_count == 10
            assert sim.elapsed_time > 0.0
        finally:
            sim.stop()

    def test_plane_loads_in_direct_mode(self):
        """World.load_plane() must succeed in DIRECT mode."""
        sim = Simulation(mode="direct")
        sim.start()
        try:
            world = World(sim)
            world.load_plane()
            # If we got here without an exception the plane loaded
        finally:
            sim.stop()

    def test_r2d2_loads_and_state_is_valid(self):
        """R2D2 robot must load and return valid base position in DIRECT mode."""
        sim = Simulation(mode="direct")
        sim.start()
        try:
            world = World(sim)
            world.load_plane()

            try:
                urdf_path = find_urdf("r2d2.urdf")
            except FileNotFoundError:
                pytest.skip("r2d2.urdf not available in pybullet_data")

            robot = Robot.load(
                str(urdf_path),
                sim=sim,
                position=(0.0, 0.0, 0.3),
                name="SmokeR2D2",
            )

            # Robot must have been assigned a valid body ID
            assert robot.body_id >= 0

            # Step the simulation a few times
            for _ in range(60):
                sim.step()

            # Base position must be a 3-tuple of floats
            pos = robot.base_position
            assert len(pos) == 3
            assert all(isinstance(v, float) for v in pos)

            # Z coordinate must be positive — robot is above the ground
            assert pos[2] > -0.1, f"Robot fell through the ground: z={pos[2]}"

            # Orientation must be a unit quaternion (4-vector, magnitude ≈ 1)
            import math
            orn = robot.base_orientation
            assert len(orn) == 4
            mag = math.sqrt(sum(v ** 2 for v in orn))
            assert abs(mag - 1.0) < 1e-4, f"Orientation quaternion is not unit: mag={mag}"

            # Speed must be non-negative
            assert robot.speed >= 0.0

        finally:
            sim.stop()

    def test_kuka_loads_and_joints_readable(self):
        """Kuka iiwa arm must load with a non-empty, readable joint set."""
        sim = Simulation(mode="direct")
        sim.start()
        try:
            world = World(sim)
            world.load_plane()

            try:
                urdf_path = find_urdf("kuka_iiwa/model.urdf")
            except FileNotFoundError:
                pytest.skip("kuka_iiwa/model.urdf not available in pybullet_data")

            robot = Robot.load(
                str(urdf_path),
                sim=sim,
                position=(0.0, 0.0, 0.0),
                fixed_base=True,
                name="SmokeKuka",
            )

            assert robot.body_id >= 0
            assert robot.num_joints > 0
            assert robot.num_controllable_joints > 0

            # Every controllable joint must return a float position
            for joint in robot.controllable_joints:
                assert isinstance(joint.position, float)

            # RL state vector must be correctly sized
            import numpy as np
            state = robot.get_state()
            assert isinstance(state, np.ndarray)
            expected_len = 13 + 2 * robot.num_controllable_joints
            assert len(state) == expected_len

        finally:
            sim.stop()

    def test_pybullet_data_path_is_accessible(self):
        """pybullet_data assets directory must exist and be readable."""
        import pathlib
        data_path = pathlib.Path(pybullet_data.getDataPath())
        assert data_path.exists(), f"pybullet_data path missing: {data_path}"
        assert (data_path / "plane.urdf").exists(), "plane.urdf missing from pybullet_data"
