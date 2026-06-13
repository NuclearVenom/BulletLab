"""Tests for bulletlab.robot.joint.Joint."""

import pytest
from bulletlab.robot.joint import JointType


class TestJointBasicProperties:
    def test_joints_have_names(self, kuka_robot):
        for name, joint in kuka_robot.joints.items():
            assert isinstance(joint.name, str)
            assert len(joint.name) > 0

    def test_joints_have_indices(self, kuka_robot):
        for name, joint in kuka_robot.joints.items():
            assert isinstance(joint.index, int)

    def test_joint_type_valid(self, kuka_robot):
        for joint in kuka_robot.joints.values():
            assert joint.joint_type is not None

    def test_fixed_joints_detected(self, kuka_robot):
        # At least some joints should be non-fixed in a typical robot
        non_fixed = [j for j in kuka_robot.joints.values() if not j.is_fixed]
        assert len(non_fixed) > 0


class TestJointStateReads:
    def test_position_is_float(self, kuka_robot, sim_with_plane):
        for joint in kuka_robot.controllable_joints[:3]:
            assert isinstance(joint.position, float)

    def test_velocity_is_float(self, kuka_robot, sim_with_plane):
        for joint in kuka_robot.controllable_joints[:3]:
            assert isinstance(joint.velocity, float)

    def test_torque_is_float(self, kuka_robot, sim_with_plane):
        for joint in kuka_robot.controllable_joints[:3]:
            assert isinstance(joint.torque, float)


class TestJointVelocityControl:
    def test_set_velocity(self, kuka_robot, sim_with_plane):
        joint = kuka_robot.controllable_joints[0]
        joint.velocity = 1.0
        for _ in range(50):
            sim_with_plane.step()
        # Joint should have moved
        assert abs(joint.position) > 0.0

    def test_velocity_setter_does_not_raise(self, kuka_robot):
        joint = kuka_robot.controllable_joints[0]
        joint.velocity = 5.0
        joint.velocity = -5.0
        joint.velocity = 0.0


class TestJointPositionControl:
    def test_set_position_moves_joint(self, kuka_robot, sim_with_plane):
        joint = kuka_robot.controllable_joints[0]
        joint.set_position(0.5)
        for _ in range(200):
            sim_with_plane.step()
        # Position should be close to target
        assert abs(joint.position - 0.5) < 0.3  # within 0.3 rad


class TestJointLimits:
    def test_limits_are_tuple_of_two_floats(self, kuka_robot):
        for joint in kuka_robot.joints.values():
            lo, hi = joint.limits
            assert isinstance(lo, float)
            assert isinstance(hi, float)


class TestJointMaxForceVelocity:
    def test_set_max_force(self, kuka_robot):
        joint = kuka_robot.controllable_joints[0]
        joint.max_force = 200.0
        assert joint.max_force == pytest.approx(200.0)

    def test_set_max_velocity(self, kuka_robot):
        joint = kuka_robot.controllable_joints[0]
        joint.max_velocity = 15.0
        assert joint.max_velocity == pytest.approx(15.0)


class TestJointEnableDisable:
    def test_enable_disable(self, kuka_robot, sim_with_plane):
        joint = kuka_robot.controllable_joints[0]
        assert joint.is_enabled
        joint.disable()
        assert not joint.is_enabled
        joint.enable()
        assert joint.is_enabled


class TestJointReset:
    def test_reset_sets_position(self, kuka_robot, sim_with_plane):
        joint = kuka_robot.controllable_joints[0]
        joint.reset(pos=1.0, vel=0.0)
        sim_with_plane.step()
        assert abs(joint.position - 1.0) < 0.01

    def test_reset_zero(self, kuka_robot, sim_with_plane):
        joint = kuka_robot.controllable_joints[0]
        joint.reset(pos=0.0, vel=0.0)
        sim_with_plane.step()
        assert abs(joint.position) < 0.01
