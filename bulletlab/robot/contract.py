"""Machine-readable robot descriptions built from BulletLab's named API."""

from __future__ import annotations

from typing import Any

from bulletlab.robot.robot import Robot


def robot_contract(robot: Robot) -> dict[str, Any]:
    """Return a JSON-serializable description of a loaded robot.

    The action order matches :meth:`Robot.apply_action`, while ``state_size``
    matches :meth:`Robot.get_state`. This makes the result useful for headless
    smoke checks and for tools that need to inspect an unfamiliar URDF without
    relying on PyBullet's integer identifiers.
    """
    joints = sorted(robot.joints.values(), key=lambda joint: joint.index)
    links = sorted(robot.links.values(), key=lambda link: link.index)
    controllable = robot.controllable_joints

    return {
        "schema_version": 1,
        "name": robot.name,
        "action": {
            "size": robot.num_controllable_joints,
            "joint_order": [joint.name for joint in controllable],
        },
        "observation": {
            "state_size": int(robot.get_state().size),
            "layout": [
                "base_position[3]",
                "base_orientation_xyzw[4]",
                "base_linear_velocity[3]",
                "base_angular_velocity[3]",
                "joint_positions[action.size]",
                "joint_velocities[action.size]",
            ],
        },
        "joints": [
            {
                "name": joint.name,
                "index": joint.index,
                "type": getattr(joint.joint_type, "name", str(joint.joint_type)),
                "controllable": not joint.is_fixed,
                "limits": list(joint.limits),
                "max_force": joint.max_force,
                "max_velocity": joint.max_velocity,
            }
            for joint in joints
        ],
        "links": [
            {
                "name": link.name,
                "index": link.index,
                "mass": link.mass,
            }
            for link in links
        ],
    }
