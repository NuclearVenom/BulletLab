"""
Tests for bulletlab.quickLaunch.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

import bulletlab
from bulletlab.quick_launch import quickLaunch


class TestQuickLaunch:
    """Test quickLaunch API and initialization logic."""

    def test_quick_launch_exported_at_top_level(self):
        """quickLaunch must be importable directly from bulletlab."""
        assert hasattr(bulletlab, "quickLaunch")
        assert callable(bulletlab.quickLaunch)

    @patch("bulletlab.robot.robot.Robot.load")
    @patch("bulletlab.core.world.World.load_plane")
    @patch("bulletlab.core.simulation.Simulation.start")
    @patch("bulletlab.core.simulation.Simulation.set_camera")
    def test_quick_launch_resolves_and_runs(
        self, mock_camera, mock_start, mock_plane, mock_robot_load
    ):
        """quickLaunch should initialize physics, world, robot, and UI."""
        mock_robot = MagicMock()
        mock_robot.name = "TestBot"
        mock_robot.joints = {}
        mock_robot.controllable_joints = []
        mock_robot.links = {}
        mock_robot.get_state.return_value = [0.0] * 6
        mock_robot.base_position = (0.0, 0.0, 0.1)
        mock_robot.speed = 0.0
        mock_robot.roll = 0.0
        mock_robot.pitch = 0.0
        mock_robot.yaw = 0.0
        mock_robot_load.return_value = mock_robot

        with patch("bulletlab.ui.BulletLabUI") as mock_ui_cls, \
             patch("bulletlab.core.simulation.Simulation.is_connected", side_effect=[True, False]):
            mock_ui = MagicMock()
            mock_ui.should_close = True
            mock_ui_cls.return_value = mock_ui

            quickLaunch("r2d2.urdf")

            mock_start.assert_called_once()
            mock_plane.assert_called_once()
            mock_robot_load.assert_called_once()
            mock_robot.auto_ground.assert_called_once_with(clearance=0.02)

    @patch("bulletlab.robot.robot.Robot._load_from_arsenal")
    @patch("bulletlab.robot.robot.Robot.load")
    @patch("bulletlab.core.world.World.load_plane")
    @patch("bulletlab.core.simulation.Simulation.start")
    @patch("bulletlab.core.simulation.Simulation.set_camera")
    def test_quick_launch_arsenal_pre_resolve(
        self, mock_camera, mock_start, mock_plane, mock_robot_load, mock_arsenal_load
    ):
        """Arsenal models must be pre-resolved before Simulation.start() opens the window."""
        call_order = []
        mock_arsenal_load.side_effect = lambda src: (call_order.append("arsenal_download"), "/tmp/bot.urdf")[1]
        mock_start.side_effect = lambda: call_order.append("sim_start")

        mock_robot = MagicMock()
        mock_robot.name = "BLem1"
        mock_robot.joints = {}
        mock_robot.controllable_joints = []
        mock_robot.links = {}
        mock_robot.get_state.return_value = []
        mock_robot.base_position = (0.0, 0.0, 0.1)
        mock_robot.speed = 0.0
        mock_robot.roll = 0.0
        mock_robot.pitch = 0.0
        mock_robot.yaw = 0.0
        mock_robot_load.return_value = mock_robot

        with patch("bulletlab.ui.BulletLabUI") as mock_ui_cls, \
             patch("bulletlab.core.simulation.Simulation.is_connected", side_effect=[True, False]):
            mock_ui = MagicMock()
            mock_ui.should_close = True
            mock_ui_cls.return_value = mock_ui

            quickLaunch("arsenal:reference_bot/BLem1")

            assert call_order == ["arsenal_download", "sim_start"], (
                "Arsenal download MUST occur before Simulation.start() opens the GUI window"
            )

    @patch("bulletlab.robot.robot.Robot.load")
    @patch("bulletlab.core.world.World.load_plane")
    @patch("bulletlab.core.simulation.Simulation.start")
    @patch("bulletlab.core.simulation.Simulation.set_camera")
    def test_quick_launch_custom_spawn_position(
        self, mock_camera, mock_start, mock_plane, mock_robot_load
    ):
        """When spawn_position is explicitly given, auto_ground is skipped."""
        mock_robot = MagicMock()
        mock_robot.name = "TestBot"
        mock_robot.joints = {}
        mock_robot.controllable_joints = []
        mock_robot.links = {}
        mock_robot.get_state.return_value = [0.0] * 6
        mock_robot.base_position = (1.0, 2.0, 3.0)
        mock_robot.speed = 0.0
        mock_robot.roll = 0.0
        mock_robot.pitch = 0.0
        mock_robot.yaw = 0.0
        mock_robot_load.return_value = mock_robot

        with patch("bulletlab.ui.BulletLabUI") as mock_ui_cls, \
             patch("bulletlab.core.simulation.Simulation.is_connected", side_effect=[True, False]):
            mock_ui = MagicMock()
            mock_ui.should_close = True
            mock_ui_cls.return_value = mock_ui

            quickLaunch("r2d2.urdf", spawn_position=(1.0, 2.0, 3.0))

            mock_robot_load.assert_called_once()
            _, kwargs = mock_robot_load.call_args
            assert kwargs["position"] == (1.0, 2.0, 3.0)
            assert kwargs["name"] == "r2d2"  # Path.stem of 'r2d2.urdf'
            mock_robot.auto_ground.assert_not_called()
