"""
BulletLab – A fast, extensible robotics experimentation framework built on PyBullet.

Developed by Ranasurya Ghosh (https://github.com/NuclearVenom/BulletLab)

BulletLab provides a high-level Python API over PyBullet, making robotics
experimentation significantly easier by exposing robots as structured Python
objects rather than raw physics engine primitives.

Quick Start::

    from bulletlab import Simulation, Robot

    sim = Simulation()
    sim.start()

    robot = Robot.load("robot.urdf", sim=sim)
    robot.joints["motor"].velocity = 15
    robot.links["wheel"].mass = 2.5

    while True:
        sim.step()
"""

from bulletlab.core.simulation import Simulation
from bulletlab.core.world import World
from bulletlab.core.camera import CameraFollow
from bulletlab.core.highlighter import RobotHighlighter
from bulletlab.robot.robot import Robot
from bulletlab.robot.joint import Joint
from bulletlab.robot.link import Link
from bulletlab.telemetry.manager import TelemetryManager
from bulletlab.logging.logger import DataLogger
from bulletlab.plotting.live_plot import LivePlot
from bulletlab.utils.math_utils import (
    euler_to_quaternion,
    quaternion_to_euler,
    axis_angle_to_quaternion,
)
from bulletlab.arsenal.exceptions import ArsenalError

__version__ = "0.2.0"
__author__ = "Ranasurya Ghosh"
__url__ = "https://github.com/NuclearVenom/BulletLab"
__license__ = "MIT"

__all__ = [
    "Simulation",
    "World",
    "CameraFollow",
    "RobotHighlighter",
    "Robot",
    "Joint",
    "Link",
    "TelemetryManager",
    "DataLogger",
    "LivePlot",
    # Math utilities
    "euler_to_quaternion",
    "quaternion_to_euler",
    "axis_angle_to_quaternion",
    # Arsenal
    "ArsenalError",
]
