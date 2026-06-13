"""Tests for bulletlab.core.simulation."""

import pytest
from bulletlab.core.simulation import Simulation


class TestSimulationLifecycle:
    def test_connect_and_disconnect(self):
        sim = Simulation(mode="direct")
        assert not sim.is_connected
        sim.start()
        assert sim.is_connected
        sim.stop()
        assert not sim.is_connected

    def test_context_manager(self):
        with Simulation(mode="direct") as sim:
            assert sim.is_connected
        assert not sim.is_connected

    def test_start_returns_self(self):
        sim = Simulation(mode="direct")
        result = sim.start()
        assert result is sim
        sim.stop()

    def test_double_start_safe(self):
        sim = Simulation(mode="direct")
        sim.start()
        sim.start()  # should not raise
        sim.stop()

    def test_stop_when_not_connected(self):
        sim = Simulation(mode="direct")
        sim.stop()  # should not raise


class TestSimulationStep:
    def test_step_increments_count(self, sim):
        assert sim.step_count == 0
        sim.step()
        assert sim.step_count == 1
        sim.step()
        assert sim.step_count == 2

    def test_elapsed_time(self, sim):
        sim.timestep = 1.0 / 240.0
        for _ in range(240):
            sim.step()
        assert abs(sim.elapsed_time - 1.0) < 1e-6

    def test_pause_stops_stepping(self, sim):
        sim.pause()
        assert sim.is_paused
        sim.step()  # should be a no-op
        assert sim.step_count == 0

    def test_resume_allows_stepping(self, sim):
        sim.pause()
        sim.resume()
        assert not sim.is_paused
        sim.step()
        assert sim.step_count == 1


class TestSimulationGravity:
    def test_default_gravity(self, sim):
        assert sim.gravity == (0.0, 0.0, -9.81)

    def test_set_gravity(self, sim):
        sim.gravity = (0.0, 0.0, -1.62)
        assert sim.gravity == (0.0, 0.0, -1.62)

    def test_moon_gravity(self, sim):
        sim.gravity = (0, 0, -1.62)
        assert sim.gravity[2] == pytest.approx(-1.62)

    def test_zero_gravity(self, sim):
        sim.gravity = (0, 0, 0)
        assert sim.gravity == (0.0, 0.0, 0.0)


class TestSimulationTimestep:
    def test_default_timestep(self, sim):
        assert sim.timestep == pytest.approx(1.0 / 240.0)

    def test_set_timestep(self, sim):
        sim.timestep = 1.0 / 480.0
        assert sim.timestep == pytest.approx(1.0 / 480.0)


class TestSimulationReset:
    def test_reset_clears_steps(self, sim):
        for _ in range(10):
            sim.step()
        assert sim.step_count == 10
        sim.reset()
        assert sim.step_count == 0

    def test_reset_clears_robots(self, sim):
        from bulletlab.robot.robot import Robot
        from bulletlab.utils.urdf_utils import find_urdf
        try:
            path = find_urdf("r2d2.urdf")
        except FileNotFoundError:
            pytest.skip("r2d2 not available")

        from bulletlab.core.world import World
        World(sim).load_plane()
        robot = Robot.load(str(path), sim=sim, position=(0, 0, 0.3))
        assert len(sim.robots) == 1
        sim.reset()
        assert len(sim.robots) == 0


class TestSimulationRobotManagement:
    def test_add_and_remove_robot(self, sim):
        class FakeRobot:
            pass

        r = FakeRobot()
        sim.add_robot(r)
        assert r in sim.robots
        sim.remove_robot(r)
        assert r not in sim.robots

    def test_add_robot_no_duplicates(self, sim):
        class FakeRobot:
            pass

        r = FakeRobot()
        sim.add_robot(r)
        sim.add_robot(r)
        assert sim.robots.count(r) == 1
