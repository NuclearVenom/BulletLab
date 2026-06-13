"""Tests for bulletlab.robot.robot.Robot."""

import math
import pytest
import numpy as np


class TestRobotLoad:
    def test_load_kuka(self, kuka_robot):
        robot = kuka_robot
        assert robot is not None
        assert robot.name == "TestKuka"
        assert robot.body_id >= 0

    def test_joints_populated(self, kuka_robot):
        assert len(kuka_robot.joints) > 0

    def test_links_populated(self, kuka_robot):
        assert len(kuka_robot.links) > 0

    def test_base_link_accessible(self, kuka_robot):
        # 'base' should always be in links
        assert "base" in kuka_robot.links

    def test_r2d2_load(self, r2d2_robot):
        assert r2d2_robot is not None
        assert len(r2d2_robot.joints) > 0

    def test_num_joints(self, kuka_robot):
        assert kuka_robot.num_joints > 0

    def test_num_controllable_joints(self, kuka_robot):
        assert kuka_robot.num_controllable_joints > 0

    def test_controllable_joints_not_fixed(self, kuka_robot):
        from bulletlab.robot.joint import JointType
        for j in kuka_robot.controllable_joints:
            assert not j.is_fixed


class TestRobotBaseState:
    def test_base_position_is_tuple3(self, r2d2_robot):
        pos = r2d2_robot.base_position
        assert len(pos) == 3
        assert all(isinstance(v, float) for v in pos)

    def test_base_orientation_is_quaternion(self, r2d2_robot):
        orn = r2d2_robot.base_orientation
        assert len(orn) == 4

    def test_base_velocity_is_tuple3(self, r2d2_robot):
        vel = r2d2_robot.base_velocity
        assert len(vel) == 3

    def test_base_angular_velocity_is_tuple3(self, r2d2_robot):
        avel = r2d2_robot.base_angular_velocity
        assert len(avel) == 3

    def test_roll_pitch_yaw_are_floats(self, r2d2_robot):
        assert isinstance(r2d2_robot.roll, float)
        assert isinstance(r2d2_robot.pitch, float)
        assert isinstance(r2d2_robot.yaw, float)

    def test_speed_non_negative(self, r2d2_robot):
        assert r2d2_robot.speed >= 0.0

    def test_initial_position_close_to_load_position(self, r2d2_robot):
        # R2D2 loaded at (0, 0, 0.3) — z may be slightly above due to plane collision
        pos = r2d2_robot.base_position
        assert abs(pos[0]) < 0.1
        assert abs(pos[1]) < 0.1


class TestRobotGetState:
    def test_get_state_is_numpy_array(self, kuka_robot):
        state = kuka_robot.get_state()
        assert isinstance(state, np.ndarray)

    def test_get_state_dtype_float64(self, kuka_robot):
        state = kuka_robot.get_state()
        assert state.dtype == np.float64

    def test_get_state_length(self, kuka_robot):
        state = kuka_robot.get_state()
        n = kuka_robot.num_controllable_joints
        expected_len = 13 + 2 * n  # 3 pos + 4 orn + 3 vel + 3 avel + 2*N
        assert len(state) == expected_len


class TestRobotApplyAction:
    def test_apply_action_correct_length(self, kuka_robot, sim_with_plane):
        n = kuka_robot.num_controllable_joints
        action = np.zeros(n)
        kuka_robot.apply_action(action)  # should not raise
        sim_with_plane.step()

    def test_apply_action_wrong_length_raises(self, kuka_robot):
        with pytest.raises(ValueError, match="Action length"):
            kuka_robot.apply_action(np.zeros(100))

    def test_apply_torques_correct_length(self, kuka_robot, sim_with_plane):
        n = kuka_robot.num_controllable_joints
        kuka_robot.apply_torques(np.zeros(n))
        sim_with_plane.step()


class TestRobotReset:
    def test_reset_returns_to_origin(self, r2d2_robot, sim_with_plane):
        # Move robot away
        for _ in range(50):
            for j in r2d2_robot.controllable_joints[:2]:
                j.velocity = 5.0
            sim_with_plane.step()

        r2d2_robot.reset(position=(0, 0, 0.3))
        pos = r2d2_robot.base_position
        assert abs(pos[0]) < 0.05
        assert abs(pos[1]) < 0.05
