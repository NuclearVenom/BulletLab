"""Tests for bulletlab.robot.link.Link."""

import pytest


class TestLinkBasicProperties:
    def test_links_have_names(self, kuka_robot):
        for name, link in kuka_robot.links.items():
            assert isinstance(link.name, str)
            assert len(link.name) > 0

    def test_links_have_indices(self, kuka_robot):
        for link in kuka_robot.links.values():
            assert isinstance(link.index, int)
            assert link.index >= -1

    def test_base_link_index_is_minus_one(self, kuka_robot):
        base = kuka_robot.links.get("base")
        assert base is not None
        assert base.index == -1


class TestLinkMass:
    def test_mass_is_positive_float(self, kuka_robot):
        for link in kuka_robot.links.values():
            assert isinstance(link.mass, float)
            assert link.mass >= 0.0

    def test_mass_setter_propagates_to_pybullet(self, kuka_robot, sim_with_plane):
        link = list(kuka_robot.links.values())[0]
        original_mass = link.mass
        link.mass = 99.0
        assert link.mass == pytest.approx(99.0)
        link.mass = original_mass  # restore

    def test_mass_all_links_readable(self, kuka_robot):
        for link in kuka_robot.links.values():
            _ = link.mass  # should not raise


class TestLinkFriction:
    def test_friction_is_float(self, kuka_robot):
        for link in kuka_robot.links.values():
            assert isinstance(link.friction, float)

    def test_friction_setter(self, kuka_robot):
        link = list(kuka_robot.links.values())[0]
        link.friction = 0.8
        assert link.friction == pytest.approx(0.8)

    def test_friction_zero(self, kuka_robot):
        link = list(kuka_robot.links.values())[0]
        link.friction = 0.0
        assert link.friction == pytest.approx(0.0)


class TestLinkRestitution:
    def test_restitution_is_float(self, kuka_robot):
        for link in kuka_robot.links.values():
            assert isinstance(link.restitution, float)

    def test_restitution_setter(self, kuka_robot):
        link = list(kuka_robot.links.values())[0]
        link.restitution = 0.5
        assert link.restitution == pytest.approx(0.5)


class TestLinkDamping:
    def test_linear_damping_is_float(self, kuka_robot):
        for link in kuka_robot.links.values():
            assert isinstance(link.linear_damping, float)

    def test_linear_damping_setter(self, kuka_robot):
        link = list(kuka_robot.links.values())[0]
        link.linear_damping = 0.05
        assert link.linear_damping == pytest.approx(0.05)

    def test_angular_damping_setter(self, kuka_robot):
        link = list(kuka_robot.links.values())[0]
        link.angular_damping = 0.05
        assert link.angular_damping == pytest.approx(0.05)

    def test_damping_shorthand(self, kuka_robot):
        link = list(kuka_robot.links.values())[0]
        link.damping = 0.1
        assert link.linear_damping == pytest.approx(0.1)
        assert link.angular_damping == pytest.approx(0.1)


class TestLinkStateReads:
    def test_position_is_tuple3(self, r2d2_robot, sim_with_plane):
        for link in list(r2d2_robot.links.values())[:3]:
            pos = link.position
            assert len(pos) == 3
            assert all(isinstance(v, float) for v in pos)

    def test_orientation_is_quaternion(self, r2d2_robot, sim_with_plane):
        link = list(r2d2_robot.links.values())[0]
        orn = link.orientation
        assert len(orn) == 4

    def test_velocity_is_tuple3(self, r2d2_robot, sim_with_plane):
        for link in list(r2d2_robot.links.values())[:3]:
            vel = link.velocity
            assert len(vel) == 3

    def test_angular_velocity_is_tuple3(self, r2d2_robot, sim_with_plane):
        link = list(r2d2_robot.links.values())[0]
        avel = link.angular_velocity
        assert len(avel) == 3

    def test_inertia_is_tuple3(self, kuka_robot):
        link = list(kuka_robot.links.values())[0]
        inertia = link.inertia
        assert len(inertia) == 3
