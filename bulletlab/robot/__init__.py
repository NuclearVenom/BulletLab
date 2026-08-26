"""
BulletLab robot subpackage.

Provides the Robot, Joint, and Link classes for interacting with simulated
robots as structured Python objects.
"""

from bulletlab.robot.robot import Robot
from bulletlab.robot.joint import Joint, JointType
from bulletlab.robot.link import Link
from bulletlab.robot.contract import robot_contract

__all__ = ["Robot", "Joint", "JointType", "Link", "robot_contract"]
