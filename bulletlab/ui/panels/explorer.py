"""
ExplorerPanel – displays the simulation scene tree.

Shows the hierarchy: Simulation → Robots → Joints / Links.
Clicking an item fires a selection callback that the PropertiesPanel
(and other panels) can subscribe to.

Example::

    from bulletlab.ui.panels.explorer import ExplorerPanel

    explorer = ExplorerPanel(sim=sim, robots=[robot])
    # In your render loop:
    explorer.render()
    selected = explorer.selected_object
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

try:
    import imgui

    _HAS_IMGUI = True
except ImportError:  # pragma: no cover
    imgui = None  # type: ignore[assignment]
    _HAS_IMGUI = False

if TYPE_CHECKING:
    from bulletlab.core.simulation import Simulation
    from bulletlab.robot.robot import Robot


class ExplorerPanel:
    """Renders a tree view of the simulation scene.

    Args:
        sim: The :class:`~bulletlab.core.simulation.Simulation` instance.
        robots: List of robots to display in the tree.
        on_select: Optional callback called with the selected object
            whenever the user clicks on a tree item.

    Example::

        explorer = ExplorerPanel(sim=sim, robots=[robot])
        explorer.render()
        selected = explorer.selected_object
    """

    def __init__(
        self,
        sim: "Simulation",
        robots: list["Robot"] | None = None,
        on_select: Callable[[Any], None] | None = None,
    ) -> None:
        self._sim = sim
        self._robots: list["Robot"] = robots or []
        self._on_select = on_select
        self._selected: Any = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def selected_object(self) -> Any:
        """The currently selected object (Robot, Joint, Link, or None)."""
        return self._selected

    def add_robot(self, robot: "Robot") -> None:
        """Add a robot to the explorer tree.

        Args:
            robot: The robot to add.
        """
        if robot not in self._robots:
            self._robots.append(robot)

    def render(self) -> None:
        """Draw the explorer panel contents.

        Must be called inside an active ImGui window context.

        Example::

            imgui.begin("Explorer")
            explorer.render()
            imgui.end()
        """
        if not _HAS_IMGUI:
            return

        # Simulation node
        sim_open = imgui.tree_node("Simulation##root")
        if imgui.is_item_clicked():
            self._select(self._sim)
        if sim_open:
            for robot in self._robots:
                self._render_robot(robot)
            imgui.tree_pop()

    def _render_robot(self, robot: "Robot") -> None:
        """Render tree node for a single robot."""
        robot_label = f"\U0001F916 {robot.name}##robot_{id(robot)}"
        robot_open = imgui.tree_node(robot_label)
        if imgui.is_item_clicked():
            self._select(robot)

        if robot_open:
            # Joints subtree
            joints_open = imgui.tree_node(f"Joints ({len(robot.joints)})##joints_{id(robot)}")
            if joints_open:
                for name, joint in robot.joints.items():
                    clicked = imgui.selectable(
                        f"  \U0001F517 {name}##joint_{id(joint)}",
                        self._selected is joint,
                    )[0]
                    if clicked:
                        self._select(joint)
                imgui.tree_pop()

            # Links subtree
            links_open = imgui.tree_node(f"Links ({len(robot.links)})##links_{id(robot)}")
            if links_open:
                for name, link in robot.links.items():
                    clicked = imgui.selectable(
                        f"  \U0001F9F1 {name}##link_{id(link)}",
                        self._selected is link,
                    )[0]
                    if clicked:
                        self._select(link)
                imgui.tree_pop()

            imgui.tree_pop()

    def _select(self, obj: Any) -> None:
        """Handle selection of an object."""
        self._selected = obj
        if self._on_select is not None:
            self._on_select(obj)

    def __repr__(self) -> str:
        return f"ExplorerPanel(robots={[r.name for r in self._robots]})"
