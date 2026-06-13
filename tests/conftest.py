"""
Shared pytest fixtures for BulletLab tests.

All tests that need a simulation run in DIRECT mode (headless) for speed and CI compatibility.
"""

from __future__ import annotations

import pytest

from bulletlab.core.simulation import Simulation


@pytest.fixture
def sim():
    """Provide a headless simulation instance for each test."""
    s = Simulation(mode="direct")
    s.start()
    yield s
    s.stop()


@pytest.fixture
def sim_with_plane(sim):
    """Provide a headless simulation with a ground plane loaded."""
    from bulletlab.core.world import World
    world = World(sim)
    world.load_plane()
    yield sim


@pytest.fixture
def kuka_robot(sim_with_plane):
    """Provide a headless simulation with the Kuka iiwa arm loaded."""
    from bulletlab.robot.robot import Robot
    from bulletlab.utils.urdf_utils import find_urdf
    try:
        path = find_urdf("kuka_iiwa/model.urdf")
    except FileNotFoundError:
        pytest.skip("kuka_iiwa URDF not available in pybullet_data")
    robot = Robot.load(str(path), sim=sim_with_plane, position=(0, 0, 0), fixed_base=True, name="TestKuka")
    yield robot


@pytest.fixture
def r2d2_robot(sim_with_plane):
    """Provide a headless simulation with R2D2 loaded."""
    from bulletlab.robot.robot import Robot
    from bulletlab.utils.urdf_utils import find_urdf
    try:
        path = find_urdf("r2d2.urdf")
    except FileNotFoundError:
        pytest.skip("r2d2 URDF not available in pybullet_data")
    robot = Robot.load(str(path), sim=sim_with_plane, position=(0, 0, 0.3), name="TestR2D2")
    yield robot
