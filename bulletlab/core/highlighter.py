"""
RobotHighlighter – hover-based joint and link highlighting for BulletLab.

When a user hovers over any UI element that corresponds to a joint or link
(slider, explorer row, properties widget, custom button), the matching 3D
part of the robot glows in the PyBullet viewport.

One-liner usage::

    from bulletlab import RobotHighlighter

    hl = RobotHighlighter(robot, sim)
    app = BulletLabUI(sim=sim, robots=[robot], highlighter=hl)

BulletLabUI handles the rest automatically — no other code needed.

Manual usage (custom panels)::

    hl.set_hover(robot.joints["wheel_left"])   # highlight a joint
    hl.set_hover(robot.links["chassis"])       # highlight a link
    hl.set_hover(None)                         # clear highlight

Developed by Ranasurya Ghosh – https://github.com/NuclearVenom/BulletLab
"""

from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING, Any

import pybullet as p

if TYPE_CHECKING:
    from bulletlab.core.simulation import Simulation
    from bulletlab.robot.robot import Robot


class RobotHighlighter:
    """Highlights joints and links in the PyBullet 3D viewport on hover.

    Attach to :class:`~bulletlab.ui.app.BulletLabUI` via ``highlighter=``
    and BulletLab automatically highlights the corresponding 3D part whenever
    the user hovers over a joint or link in the Explorer, Properties panel,
    or any interactive widget.

    Args:
        robot: The robot whose parts will be highlighted.
        sim: The :class:`~bulletlab.core.simulation.Simulation` instance.
        color: RGBA highlight colour. Default: orange ``(1.0, 0.55, 0.05, 1.0)``.
        pulse: If ``True``, the highlight colour pulses (breathes) gently.
               Default: ``True``.

    Example::

        from bulletlab import Simulation, Robot, RobotHighlighter
        from bulletlab.ui import BulletLabUI

        sim = Simulation(mode="gui").start()
        robot = Robot.load("kuka_iiwa/model.urdf", sim=sim)

        # One-liner — attach to UI and it works automatically
        hl = RobotHighlighter(robot, sim)
        app = BulletLabUI(sim=sim, robots=[robot], highlighter=hl)
    """

    def __init__(
        self,
        robot: "Robot",
        sim: "Simulation",
        *,
        color: tuple[float, float, float, float] = (1.0, 0.55, 0.05, 1.0),
        pulse: bool = True,
    ) -> None:
        self._robot    = robot
        self._sim      = sim
        self._color    = color
        self._pulse    = pulse

        # PyBullet IDs
        self._body_id  = robot._body_id
        self._cid      = sim.client_id

        # Highlighted state
        self._current: Any = None     # currently highlighted obj
        self._pending: Any = None     # set during a frame by panels/widgets
        self._saved_colors: dict[int, list] = {}  # link_index → original color list

    # ------------------------------------------------------------------
    # Frame lifecycle  (called by BulletLabUI.step())
    # ------------------------------------------------------------------

    def begin_frame(self) -> None:
        """Reset the pending hover target at the start of each UI frame.

        Called automatically by :class:`~bulletlab.ui.app.BulletLabUI`.
        """
        self._pending = None

    def end_frame(self) -> None:
        """Commit the pending hover target and update 3D highlights.

        Called automatically by :class:`~bulletlab.ui.app.BulletLabUI`.
        """
        if self._pending is not self._current:
            # Clear old highlight
            if self._current is not None:
                self._clear_obj(self._current)
            self._current = self._pending
            # Apply new highlight
            if self._current is not None:
                self._apply_obj(self._current)

        # Pulse: re-apply colour every frame when something is highlighted
        elif self._current is not None and self._pulse:
            self._apply_obj(self._current)

    # ------------------------------------------------------------------
    # Public API for panels / custom widgets
    # ------------------------------------------------------------------

    def set_hover(self, obj: Any) -> None:
        """Signal that *obj* is currently being hovered.

        Call this right after any ImGui widget that corresponds to a Joint
        or Link when ``imgui.is_item_hovered()`` returns ``True``.

        Args:
            obj: A :class:`~bulletlab.robot.joint.Joint`,
                 :class:`~bulletlab.robot.link.Link`, or ``None`` to clear.

        Example::

            imgui.slider_float("Velocity", joint.velocity, -20, 20)
            if imgui.is_item_hovered():
                hl.set_hover(joint)
        """
        self._pending = obj

    def clear(self) -> None:
        """Immediately remove all highlights from the robot.

        Example::

            hl.clear()
        """
        if self._current is not None:
            self._clear_obj(self._current)
        self._current = None
        self._pending = None

    @property
    def color(self) -> tuple[float, float, float, float]:
        """RGBA highlight colour."""
        return self._color

    @color.setter
    def color(self, value: tuple[float, float, float, float]) -> None:
        self._color = tuple(value)

    @property
    def pulse(self) -> bool:
        """Whether the highlight colour pulses/breathes."""
        return self._pulse

    @pulse.setter
    def pulse(self, value: bool) -> None:
        self._pulse = bool(value)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_link_index(self, obj: Any) -> int | None:
        """Return the PyBullet link index for a Joint or Link object."""
        type_name = type(obj).__name__
        if type_name == "Joint":
            return obj.index        # joint index == child link index in PyBullet
        if type_name == "Link":
            return obj.index        # -1 for base link, ≥0 for others
        return None

    def _get_pulse_color(self) -> tuple[float, float, float, float]:
        """Return the highlight colour, potentially modulated by a pulse."""
        if not self._pulse:
            return self._color
        t = time.time()
        # Gentle sinusoidal pulse between 70% and 100% brightness
        scale = 0.70 + 0.30 * (0.5 + 0.5 * math.sin(t * 5.0))
        r, g, b, a = self._color
        return (r * scale, g * scale, b * scale, a)

    def _get_original_color(self, link_index: int) -> list | None:
        """Query PyBullet for the current visual colour of a link."""
        try:
            shapes = p.getVisualShapeData(
                self._body_id, physicsClientId=self._cid
            )
            for shape in shapes:
                if shape[1] == link_index:
                    return list(shape[7])   # [r, g, b, a]
        except Exception:
            pass
        return None

    def _apply_obj(self, obj: Any) -> None:
        """Apply highlight colour to the 3D link corresponding to *obj*."""
        link_index = self._resolve_link_index(obj)
        if link_index is None:
            return
        try:
            # Save original colour once (first highlight)
            if link_index not in self._saved_colors:
                orig = self._get_original_color(link_index)
                self._saved_colors[link_index] = orig or [0.7, 0.7, 0.7, 1.0]

            col = self._get_pulse_color()
            p.changeVisualShape(
                self._body_id,
                link_index,
                rgbaColor=list(col),
                physicsClientId=self._cid,
            )
        except Exception:
            pass   # non-fatal — 3D viewport may not have visual shapes

    def _clear_obj(self, obj: Any) -> None:
        """Restore the original colour of the 3D link for *obj*."""
        link_index = self._resolve_link_index(obj)
        if link_index is None:
            return
        try:
            orig = self._saved_colors.get(link_index, [0.7, 0.7, 0.7, 1.0])
            p.changeVisualShape(
                self._body_id,
                link_index,
                rgbaColor=orig,
                physicsClientId=self._cid,
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        current_name = getattr(self._current, "name", None)
        return (
            f"RobotHighlighter(robot={self._robot.name!r}, "
            f"current={current_name!r}, pulse={self._pulse})"
        )
