"""
PropertiesPanel – editable property inspector for the selected object.

Detects the type of the selected object (Simulation, Robot, Joint, or Link)
and renders appropriate editable fields. All changes are applied immediately
to the simulation.

Example::

    from bulletlab.ui.panels.properties import PropertiesPanel

    props = PropertiesPanel()
    props.set_target(robot.links["wheel"])
    props.render()
"""

from __future__ import annotations

import math
from typing import Any, TYPE_CHECKING

try:
    import imgui

    _HAS_IMGUI = True
except ImportError:  # pragma: no cover
    imgui = None  # type: ignore[assignment]
    _HAS_IMGUI = False

if TYPE_CHECKING:
    from bulletlab.core.simulation import Simulation
    from bulletlab.robot.robot import Robot
    from bulletlab.robot.joint import Joint
    from bulletlab.robot.link import Link


class PropertiesPanel:
    """Renders editable properties for the currently selected object.

    Automatically detects whether the target is a :class:`~bulletlab.core.simulation.Simulation`,
    :class:`~bulletlab.robot.robot.Robot`, :class:`~bulletlab.robot.joint.Joint`, or
    :class:`~bulletlab.robot.link.Link` and renders the appropriate fields.

    Example::

        props = PropertiesPanel()
        props.set_target(selected_object)
        props.render()
    """

    def __init__(self, highlighter: Any | None = None) -> None:
        self._target: Any = None
        self._highlighter = highlighter

    def set_target(self, obj: Any) -> None:
        """Set the object whose properties will be displayed.

        Args:
            obj: A Simulation, Robot, Joint, Link, or ``None`` to clear.

        Example::

            props.set_target(robot.joints["wheel_left"])
        """
        self._target = obj

    def render(self) -> None:
        """Draw the properties panel contents.

        Must be called inside an active ImGui window context.
        """
        if not _HAS_IMGUI:
            return

        if self._target is None:
            imgui.text_colored("Select an item in the Explorer.", 0.5, 0.5, 0.5, 1.0)
            return

        # Route to appropriate renderer
        type_name = type(self._target).__name__
        imgui.text(f"Type: {type_name}")
        imgui.separator()

        if type_name == "Simulation":
            self._render_simulation(self._target)
        elif type_name == "Robot":
            self._render_robot(self._target)
        elif type_name == "Joint":
            self._render_joint(self._target)
        elif type_name == "Link":
            self._render_link(self._target)
        else:
            imgui.text(str(self._target))

    def _check_hover(self, obj: Any) -> None:
        """Call after any widget — highlights *obj* in the 3D view if hovered."""
        if self._highlighter is not None and imgui.is_item_hovered():
            self._highlighter.set_hover(obj)

    # ------------------------------------------------------------------
    # Simulation properties
    # ------------------------------------------------------------------

    def _render_simulation(self, sim: "Simulation") -> None:
        imgui.text(f"Status: {'Paused' if sim.is_paused else 'Running'}")
        imgui.text(f"Steps: {sim.step_count}")
        imgui.text(f"Sim Time: {sim.elapsed_time:.3f} s")
        imgui.separator()

        # Gravity
        gx, gy, gz = sim.gravity
        changed_gz, new_gz = imgui.drag_float("Gravity Z##sim_gz", gz, 0.1, -20.0, 20.0)
        if changed_gz:
            sim.gravity = (gx, gy, new_gz)

        # Timestep
        changed_ts, new_ts = imgui.drag_float("Timestep##sim_ts", sim.timestep, 0.0001, 0.0001, 0.1, "%.5f")
        if changed_ts:
            sim.timestep = float(new_ts)

        imgui.separator()
        if sim.is_paused:
            if imgui.button("Resume##sim_resume"):
                sim.resume()
        else:
            if imgui.button("Pause##sim_pause"):
                sim.pause()
        imgui.same_line()
        if imgui.button("Reset##sim_reset"):
            sim.reset()

    # ------------------------------------------------------------------
    # Robot properties
    # ------------------------------------------------------------------

    def _render_robot(self, robot: "Robot") -> None:
        imgui.text(f"Name: {robot.name}")
        imgui.text(f"Joints: {robot.num_joints}  (controllable: {robot.num_controllable_joints})")
        imgui.text(f"Links: {len(robot.links)}")
        imgui.separator()

        pos = robot.base_position
        vel = robot.base_velocity
        roll_deg = math.degrees(robot.roll)
        pitch_deg = math.degrees(robot.pitch)
        yaw_deg = math.degrees(robot.yaw)

        imgui.text(f"Position:  ({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")
        imgui.text(f"Velocity:  ({vel[0]:.3f}, {vel[1]:.3f}, {vel[2]:.3f})")
        imgui.text(f"Roll:  {roll_deg:.2f}°")
        imgui.text(f"Pitch: {pitch_deg:.2f}°")
        imgui.text(f"Yaw:   {yaw_deg:.2f}°")
        imgui.text(f"Speed: {robot.speed:.3f} m/s")
        imgui.separator()

        if imgui.button("Reset Robot##robot_reset"):
            robot.reset()

    # ------------------------------------------------------------------
    # Joint properties
    # ------------------------------------------------------------------

    def _render_joint(self, joint: "Joint") -> None:
        imgui.text(f"Name: {joint.name}")
        imgui.text(f"Index: {joint.index}")
        imgui.text(f"Type: {joint.joint_type.name if hasattr(joint.joint_type, 'name') else joint.joint_type}")
        imgui.separator()

        imgui.text(f"Position: {joint.position:.4f} rad")
        imgui.text(f"Velocity: {joint.velocity:.4f} rad/s")
        imgui.text(f"Torque:   {joint.torque:.4f} N·m")
        lo, hi = joint.limits
        imgui.text(f"Limits: [{lo:.3f}, {hi:.3f}]")
        imgui.separator()

        # Max force
        changed_mf, new_mf = imgui.drag_float(
            "Max Force##jnt_mf", joint.max_force, 1.0, 0.0, 5000.0
        )
        self._check_hover(joint)
        if changed_mf:
            joint.max_force = float(new_mf)

        # Max velocity
        changed_mv, new_mv = imgui.drag_float(
            "Max Velocity##jnt_mv", joint.max_velocity, 0.1, 0.0, 200.0
        )
        self._check_hover(joint)
        if changed_mv:
            joint.max_velocity = float(new_mv)

        imgui.separator()

        # Target velocity control
        changed_vel, new_vel = imgui.drag_float(
            "Target Velocity##jnt_vel", joint.velocity, 0.1, -200.0, 200.0
        )
        self._check_hover(joint)
        if changed_vel:
            joint.velocity = float(new_vel)

        # Position control
        lo2, hi2 = joint.limits
        range_lo = lo2 if lo2 != 0.0 or hi2 != 0.0 else -6.28
        range_hi = hi2 if lo2 != 0.0 or hi2 != 0.0 else 6.28
        
        if joint.is_pinned:
            imgui.push_style_color(imgui.COLOR_SLIDER_GRAB, 0.9, 0.2, 0.2, 1.0)
            imgui.push_style_color(imgui.COLOR_SLIDER_GRAB_ACTIVE, 1.0, 0.3, 0.3, 1.0)
            
        changed_pos, new_pos = imgui.slider_float(
            "Target Position##jnt_pos", joint.position, range_lo, range_hi
        )
        
        if joint.is_pinned:
            imgui.pop_style_color(2)
            
        self._check_hover(joint)
        if changed_pos:
            joint.set_position(float(new_pos))

        imgui.separator()
        if imgui.button("Reset Joint##jnt_reset"):
            joint.reset()
        self._check_hover(joint)
        imgui.same_line()
        if joint.is_enabled:
            if imgui.button("Disable##jnt_disable"):
                joint.disable()
            self._check_hover(joint)
        else:
            if imgui.button("Enable##jnt_enable"):
                joint.enable()
            self._check_hover(joint)

    # ------------------------------------------------------------------
    # Link properties
    # ------------------------------------------------------------------

    def _render_link(self, link: "Link") -> None:
        imgui.text(f"Name: {link.name}")
        imgui.text(f"Index: {link.index}")
        imgui.separator()

        # Mass
        changed_mass, new_mass = imgui.drag_float(
            "Mass (kg)##lnk_mass", link.mass, 0.01, 0.0001, 1000.0
        )
        self._check_hover(link)
        if changed_mass:
            link.mass = float(new_mass)

        # Friction
        changed_fric, new_fric = imgui.drag_float(
            "Lateral Friction##lnk_fric", link.friction, 0.01, 0.0, 10.0
        )
        self._check_hover(link)
        if changed_fric:
            link.friction = float(new_fric)

        # Restitution
        changed_rest, new_rest = imgui.slider_float(
            "Restitution##lnk_rest", link.restitution, 0.0, 1.0
        )
        self._check_hover(link)
        if changed_rest:
            link.restitution = float(new_rest)

        # Linear damping
        changed_ld, new_ld = imgui.drag_float(
            "Linear Damping##lnk_ld", link.linear_damping, 0.001, 0.0, 10.0
        )
        self._check_hover(link)
        if changed_ld:
            link.linear_damping = float(new_ld)

        # Angular damping
        changed_ad, new_ad = imgui.drag_float(
            "Angular Damping##lnk_ad", link.angular_damping, 0.001, 0.0, 10.0
        )
        self._check_hover(link)
        if changed_ad:
            link.angular_damping = float(new_ad)

        imgui.separator()
        pos = link.position
        vel = link.velocity
        imgui.text(f"Position: ({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")
        imgui.text(f"Velocity: ({vel[0]:.3f}, {vel[1]:.3f}, {vel[2]:.3f})")

    def __repr__(self) -> str:
        return f"PropertiesPanel(target={type(self._target).__name__ if self._target else None})"
