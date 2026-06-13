"""Tests for bulletlab.utils (math_utils, urdf_utils, timer)."""

import math
import pytest
import numpy as np

from bulletlab.utils.math_utils import (
    quaternion_to_euler,
    euler_to_quaternion,
    normalize,
    clamp,
    lerp,
    wrap_angle,
    vec3_magnitude,
)
from bulletlab.utils.timer import SimTimer
from bulletlab.utils.urdf_utils import find_urdf, get_pybullet_data_path, list_available_urdfs


class TestQuaternionToEuler:
    def test_identity_quaternion(self):
        roll, pitch, yaw = quaternion_to_euler((0, 0, 0, 1))
        assert roll == pytest.approx(0.0, abs=1e-6)
        assert pitch == pytest.approx(0.0, abs=1e-6)
        assert yaw == pytest.approx(0.0, abs=1e-6)

    def test_90_degrees_yaw(self):
        # 90° yaw around Z = quaternion (0, 0, sin(45°), cos(45°))
        s = math.sin(math.pi / 4)
        c = math.cos(math.pi / 4)
        roll, pitch, yaw = quaternion_to_euler((0, 0, s, c))
        assert yaw == pytest.approx(math.pi / 2, abs=1e-5)
        assert roll == pytest.approx(0.0, abs=1e-5)

    def test_returns_tuple_of_3(self):
        result = quaternion_to_euler((0, 0, 0, 1))
        assert len(result) == 3


class TestEulerToQuaternion:
    def test_zero_euler_gives_identity(self):
        q = euler_to_quaternion(0.0, 0.0, 0.0)
        assert q[3] == pytest.approx(1.0, abs=1e-6)  # w
        assert q[0] == pytest.approx(0.0, abs=1e-6)  # x
        assert q[1] == pytest.approx(0.0, abs=1e-6)  # y
        assert q[2] == pytest.approx(0.0, abs=1e-6)  # z

    def test_returns_unit_quaternion(self):
        q = euler_to_quaternion(0.1, 0.2, 0.3)
        mag = math.sqrt(sum(v ** 2 for v in q))
        assert mag == pytest.approx(1.0, abs=1e-6)


class TestRoundTrip:
    def test_euler_quaternion_roundtrip(self):
        for roll, pitch, yaw in [(0.1, 0.2, 0.3), (-0.5, 0.0, 1.0), (0.0, 0.5, -0.8)]:
            q = euler_to_quaternion(roll, pitch, yaw)
            r2, p2, y2 = quaternion_to_euler(q)
            assert r2 == pytest.approx(roll, abs=1e-5)
            assert p2 == pytest.approx(pitch, abs=1e-5)
            assert y2 == pytest.approx(yaw, abs=1e-5)


class TestNormalize:
    def test_unit_vector_unchanged(self):
        v = [1.0, 0.0, 0.0]
        result = normalize(v)
        assert result[0] == pytest.approx(1.0)

    def test_general_vector(self):
        v = [3.0, 4.0, 0.0]
        result = normalize(v)
        mag = np.linalg.norm(result)
        assert mag == pytest.approx(1.0, abs=1e-6)

    def test_zero_vector_returns_zero(self):
        result = normalize([0.0, 0.0, 0.0])
        assert np.allclose(result, [0.0, 0.0, 0.0])

    def test_returns_numpy_array(self):
        result = normalize([1.0, 2.0, 3.0])
        assert isinstance(result, np.ndarray)


class TestClamp:
    def test_within_range(self):
        assert clamp(5.0, 0.0, 10.0) == pytest.approx(5.0)

    def test_below_min(self):
        assert clamp(-5.0, 0.0, 10.0) == pytest.approx(0.0)

    def test_above_max(self):
        assert clamp(15.0, 0.0, 10.0) == pytest.approx(10.0)

    def test_at_boundary(self):
        assert clamp(0.0, 0.0, 10.0) == pytest.approx(0.0)
        assert clamp(10.0, 0.0, 10.0) == pytest.approx(10.0)


class TestLerp:
    def test_zero(self):
        assert lerp(0.0, 10.0, 0.0) == pytest.approx(0.0)

    def test_one(self):
        assert lerp(0.0, 10.0, 1.0) == pytest.approx(10.0)

    def test_half(self):
        assert lerp(0.0, 10.0, 0.5) == pytest.approx(5.0)

    def test_negative_range(self):
        assert lerp(-5.0, 5.0, 0.5) == pytest.approx(0.0)


class TestWrapAngle:
    def test_zero(self):
        assert wrap_angle(0.0) == pytest.approx(0.0)

    def test_pi(self):
        assert abs(wrap_angle(math.pi)) <= math.pi + 1e-6

    def test_wraps_positive(self):
        result = wrap_angle(math.pi * 3)
        assert abs(result) <= math.pi + 1e-6

    def test_wraps_negative(self):
        result = wrap_angle(-math.pi * 3)
        assert abs(result) <= math.pi + 1e-6


class TestVec3Magnitude:
    def test_unit_vector(self):
        assert vec3_magnitude([1.0, 0.0, 0.0]) == pytest.approx(1.0)

    def test_345_triangle(self):
        assert vec3_magnitude([3.0, 4.0, 0.0]) == pytest.approx(5.0)

    def test_zero_vector(self):
        assert vec3_magnitude([0.0, 0.0, 0.0]) == pytest.approx(0.0)


class TestSimTimer:
    def test_initial_state(self):
        timer = SimTimer(timestep=1.0 / 240.0)
        assert timer.step_count == 0
        assert timer.sim_time == pytest.approx(0.0)

    def test_tick_increments_count(self):
        timer = SimTimer()
        timer.tick()
        assert timer.step_count == 1

    def test_sim_time(self):
        timer = SimTimer(timestep=0.01)
        for _ in range(10):
            timer.tick()
        assert timer.sim_time == pytest.approx(0.1, abs=1e-9)

    def test_wall_time_positive(self):
        timer = SimTimer()
        timer.tick()
        assert timer.wall_time >= 0.0

    def test_reset(self):
        timer = SimTimer()
        for _ in range(100):
            timer.tick()
        timer.reset()
        assert timer.step_count == 0
        assert timer.sim_time == pytest.approx(0.0)

    def test_timestep_setter(self):
        timer = SimTimer(timestep=0.01)
        timer.timestep = 0.02
        assert timer.timestep == pytest.approx(0.02)


class TestUrdfUtils:
    def test_get_pybullet_data_path_exists(self):
        path = get_pybullet_data_path()
        assert path.exists()

    def test_find_plane_urdf(self):
        path = find_urdf("plane.urdf")
        assert path.exists()
        assert path.suffix == ".urdf"

    def test_find_r2d2_urdf(self):
        try:
            path = find_urdf("r2d2.urdf")
            assert path.exists()
        except FileNotFoundError:
            pytest.skip("r2d2.urdf not in pybullet_data")

    def test_find_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            find_urdf("definitely_does_not_exist_xyz_123.urdf")

    def test_list_available_urdfs_not_empty(self):
        urdfs = list_available_urdfs()
        assert len(urdfs) > 0

    def test_list_available_urdfs_are_strings(self):
        urdfs = list_available_urdfs(10)
        for u in urdfs:
            assert isinstance(u, str)
