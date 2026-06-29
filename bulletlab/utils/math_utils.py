"""
Mathematical utilities for BulletLab.

Provides quaternion/Euler conversion, vector normalization, clamping,
and linear interpolation — all without external dependencies beyond NumPy.

Example::

    from bulletlab.utils.math_utils import (
        quaternion_to_euler, euler_to_quaternion, axis_angle_to_quaternion
    )

    roll, pitch, yaw = quaternion_to_euler((0, 0, 0, 1))
    q = euler_to_quaternion(0.1, 0.2, 0.3)
    q2 = axis_angle_to_quaternion((0, 0, 1), 90)   # 90° around Z
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np


def quaternion_to_euler(
    q: Sequence[float],
) -> tuple[float, float, float]:
    """Convert a quaternion to Euler angles (roll, pitch, yaw).

    Uses the ZYX (yaw-pitch-roll) convention, matching PyBullet's
    ``getEulerFromQuaternion``.

    Args:
        q: Quaternion ``(x, y, z, w)``.

    Returns:
        Euler angles ``(roll, pitch, yaw)`` in radians.

    Example::

        roll, pitch, yaw = quaternion_to_euler(robot.base_orientation)
    """
    x, y, z, w = float(q[0]), float(q[1]), float(q[2]), float(q[3])

    # Roll (rotation around X)
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # Pitch (rotation around Y)
    sinp = 2.0 * (w * y - z * x)
    sinp = max(-1.0, min(1.0, sinp))  # clamp for numerical safety
    pitch = math.asin(sinp)

    # Yaw (rotation around Z)
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return (roll, pitch, yaw)


def euler_to_quaternion(
    roll: float,
    pitch: float,
    yaw: float,
) -> tuple[float, float, float, float]:
    """Convert Euler angles (roll, pitch, yaw) to a quaternion.

    Uses the ZYX (yaw-pitch-roll) convention, matching PyBullet's
    ``getQuaternionFromEuler``.

    Args:
        roll: Rotation around X axis in radians.
        pitch: Rotation around Y axis in radians.
        yaw: Rotation around Z axis in radians.

    Returns:
        Quaternion ``(x, y, z, w)``.

    Example::

        q = euler_to_quaternion(0.0, 0.0, math.pi / 2)
    """
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)

    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy

    return (x, y, z, w)


def axis_angle_to_quaternion(
    axis: "Sequence[float]",
    angle_deg: float,
) -> tuple[float, float, float, float]:
    """Convert an axis-angle rotation to a quaternion.

    The axis does **not** need to be pre-normalised.

    Args:
        axis: Rotation axis ``(ax, ay, az)``.
        angle_deg: Rotation angle in **degrees**.

    Returns:
        Unit quaternion ``(x, y, z, w)``.

    Example::

        # 90° around the Z axis (yaw)
        q = axis_angle_to_quaternion((0, 0, 1), 90)

        # Tilt 30° forward (nose-down)
        q = axis_angle_to_quaternion((0, 1, 0), 30)
    """
    ax, ay, az = float(axis[0]), float(axis[1]), float(axis[2])
    length = math.sqrt(ax ** 2 + ay ** 2 + az ** 2)
    if length < 1e-9:
        return (0.0, 0.0, 0.0, 1.0)   # identity
    ax, ay, az = ax / length, ay / length, az / length
    half = math.radians(angle_deg) / 2.0
    s = math.sin(half)
    return (ax * s, ay * s, az * s, math.cos(half))

def normalize(v: Sequence[float]) -> np.ndarray:
    """Return the unit vector of a vector.

    Args:
        v: Input vector (any length).

    Returns:
        Unit vector as a NumPy array, or the zero vector if norm is zero.

    Example::

        direction = normalize([1.0, 2.0, 3.0])
    """
    arr = np.asarray(v, dtype=np.float64)
    norm = np.linalg.norm(arr)
    if norm == 0.0:
        return arr
    return arr / norm


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp a scalar value to the range ``[lo, hi]``.

    Args:
        value: Input value.
        lo: Lower bound.
        hi: Upper bound.

    Returns:
        Clamped value.

    Example::

        safe_speed = clamp(desired_speed, -10.0, 10.0)
    """
    return max(float(lo), min(float(hi), float(value)))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between two scalar values.

    Args:
        a: Start value.
        b: End value.
        t: Interpolation parameter in ``[0, 1]``.

    Returns:
        Interpolated value ``a + t * (b - a)``.

    Example::

        mid = lerp(0.0, 10.0, 0.5)   # → 5.0
    """
    return float(a) + float(t) * (float(b) - float(a))


def wrap_angle(angle: float) -> float:
    """Wrap an angle to the range ``[-π, π]``.

    Args:
        angle: Angle in radians.

    Returns:
        Wrapped angle in radians.

    Example::

        wrapped = wrap_angle(4.0)   # → 4.0 - 2π ≈ -2.28
    """
    return math.atan2(math.sin(angle), math.cos(angle))


def vec3_magnitude(v: Sequence[float]) -> float:
    """Return the magnitude (L2 norm) of a 3D vector.

    Args:
        v: Vector ``(x, y, z)``.

    Returns:
        Scalar magnitude.

    Example::

        speed = vec3_magnitude(robot.base_velocity)
    """
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
