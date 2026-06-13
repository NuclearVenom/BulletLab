"""
Widget helper functions for building BulletLab custom panels.

Provides a minimal, boilerplate-free API for common ImGui widgets.
All functions must be called from within an ImGui window context (i.e.,
between imgui.begin() and imgui.end()).

Example::

    from bulletlab.ui import widgets as ui

    @app.custom_panel("My Controls")
    def my_panel():
        ui.button("Reset", robot.reset)
        ui.slider("Wheel Mass", robot.links["wheel"].mass, 0.1, 20,
                  setter=lambda v: setattr(robot.links["wheel"], "mass", v))
        ui.checkbox("Motors On", lambda: motors_on,
                    setter=lambda v: set_motors(v))
        ui.text("Speed", f"{robot.speed:.2f} m/s")
"""

from __future__ import annotations

from typing import Any, Callable, Optional

# ImGui is optional — graceful fallback
try:
    import imgui

    _HAS_IMGUI = True
except ImportError:  # pragma: no cover
    imgui = None  # type: ignore[assignment]
    _HAS_IMGUI = False


def _check_imgui() -> bool:
    """Return True if imgui is available, warn otherwise."""
    if not _HAS_IMGUI:
        return False
    return True


# ------------------------------------------------------------------
# Basic widgets
# ------------------------------------------------------------------


def button(label: str, callback: Callable[[], Any] | None = None) -> bool:
    """Render a clickable button.

    Args:
        label: Button text label.
        callback: Function to call when the button is clicked.

    Returns:
        ``True`` if the button was clicked this frame.

    Example::

        ui.button("Reset Robot", robot.reset)
    """
    if not _check_imgui():
        return False
    clicked = imgui.button(label)
    if clicked and callback is not None:
        callback()
    return clicked


def text(label: str, value: Any = "") -> None:
    """Render a read-only text label with an optional value.

    Args:
        label: Field label.
        value: Value to display (converted to string).

    Example::

        ui.text("Speed", f"{robot.speed:.2f} m/s")
    """
    if not _check_imgui():
        return
    if value != "":
        imgui.text(f"{label}: {value}")
    else:
        imgui.text(str(label))


def separator(label: str = "") -> None:
    """Render a horizontal separator, optionally with a label.

    Args:
        label: Optional section label.

    Example::

        ui.separator("Physics")
    """
    if not _check_imgui():
        return
    imgui.separator()
    if label:
        imgui.text(label)


def same_line() -> None:
    """Place the next widget on the same line."""
    if _check_imgui():
        imgui.same_line()


# ------------------------------------------------------------------
# Input widgets
# ------------------------------------------------------------------


def slider(
    label: str,
    getter: Callable[[], float] | float,
    min_val: float,
    max_val: float,
    setter: Callable[[float], None] | None = None,
    fmt: str = "%.3f",
) -> float:
    """Render a float slider.

    Args:
        label: Widget label.
        getter: Current value or a callable returning the current value.
        min_val: Minimum value.
        max_val: Maximum value.
        setter: Called with the new value when the slider changes.
        fmt: Printf format string for display.

    Returns:
        Current slider value.

    Example::

        ui.slider("Wheel Mass", lambda: robot.links["wheel"].mass, 0.1, 20,
                  setter=lambda v: setattr(robot.links["wheel"], "mass", v))
    """
    if not _check_imgui():
        return 0.0
    current = float(getter()) if callable(getter) else float(getter)
    changed, new_val = imgui.slider_float(label, current, min_val, max_val, fmt)
    if changed and setter is not None:
        setter(float(new_val))
    return float(new_val) if changed else current


def drag_float(
    label: str,
    getter: Callable[[], float] | float,
    setter: Callable[[float], None] | None = None,
    speed: float = 0.1,
    min_val: float = 0.0,
    max_val: float = 0.0,
    fmt: str = "%.3f",
) -> float:
    """Render a drag-to-edit float field.

    Args:
        label: Widget label.
        getter: Current value or callable returning current value.
        setter: Called with the new value when changed.
        speed: Drag sensitivity.
        min_val: Minimum value (0 = no clamp).
        max_val: Maximum value (0 = no clamp).
        fmt: Printf format string for display.

    Returns:
        Current value.

    Example::

        ui.drag_float("Mass", lambda: link.mass, setter=lambda v: setattr(link, "mass", v))
    """
    if not _check_imgui():
        return 0.0
    current = float(getter()) if callable(getter) else float(getter)
    changed, new_val = imgui.drag_float(label, current, speed, min_val, max_val, fmt)
    if changed and setter is not None:
        setter(float(new_val))
    return float(new_val) if changed else current


def input_float(
    label: str,
    getter: Callable[[], float] | float,
    setter: Callable[[float], None] | None = None,
    step: float = 0.1,
    fmt: str = "%.3f",
) -> float:
    """Render a float input field.

    Args:
        label: Widget label.
        getter: Current value or callable.
        setter: Called with the new value when committed.
        step: Increment step for +/- buttons.
        fmt: Display format string.

    Returns:
        Current value.

    Example::

        ui.input_float("Friction", lambda: link.friction,
                       setter=lambda v: setattr(link, "friction", v))
    """
    if not _check_imgui():
        return 0.0
    current = float(getter()) if callable(getter) else float(getter)
    changed, new_val = imgui.input_float(label, current, step, step * 10, fmt)
    if changed and setter is not None:
        setter(float(new_val))
    return float(new_val) if changed else current


def checkbox(
    label: str,
    getter: Callable[[], bool] | bool,
    setter: Callable[[bool], None] | None = None,
) -> bool:
    """Render a checkbox.

    Args:
        label: Widget label.
        getter: Current state or callable returning current state.
        setter: Called with the new state when toggled.

    Returns:
        Current checkbox state.

    Example::

        ui.checkbox("Motors Enabled", lambda: motors_on,
                    setter=lambda v: set_motors(v))
    """
    if not _check_imgui():
        return False
    current = bool(getter()) if callable(getter) else bool(getter)
    changed, new_val = imgui.checkbox(label, current)
    if changed and setter is not None:
        setter(bool(new_val))
    return bool(new_val) if changed else current


def color_edit(
    label: str,
    getter: Callable[[], tuple[float, float, float]] | tuple[float, float, float],
    setter: Callable[[tuple[float, float, float]], None] | None = None,
) -> tuple[float, float, float]:
    """Render an RGB color picker.

    Args:
        label: Widget label.
        getter: Current color ``(r, g, b)`` normalized to [0, 1] or callable.
        setter: Called with the new color when changed.

    Returns:
        Current color ``(r, g, b)``.

    Example::

        ui.color_edit("Light Color", lambda: color, setter=lambda c: set_color(c))
    """
    if not _check_imgui():
        return (1.0, 1.0, 1.0)
    current = tuple(getter()) if callable(getter) else tuple(getter)
    r, g, b = float(current[0]), float(current[1]), float(current[2])
    changed, (nr, ng, nb) = imgui.color_edit3(label, r, g, b)
    result = (float(nr), float(ng), float(nb))
    if changed and setter is not None:
        setter(result)
    return result if changed else (r, g, b)


def combo(
    label: str,
    items: list[str],
    getter: Callable[[], int] | int,
    setter: Callable[[int], None] | None = None,
) -> int:
    """Render a dropdown combo box.

    Args:
        label: Widget label.
        items: List of selectable items.
        getter: Current selected index or callable.
        setter: Called with new index when changed.

    Returns:
        Current selected index.

    Example::

        ui.combo("Mode", ["Velocity", "Position", "Torque"], lambda: mode_idx,
                 setter=lambda i: set_mode(i))
    """
    if not _check_imgui():
        return 0
    current = int(getter()) if callable(getter) else int(getter)
    changed, new_idx = imgui.combo(label, current, items)
    if changed and setter is not None:
        setter(int(new_idx))
    return int(new_idx) if changed else current


def collapsing_header(label: str, default_open: bool = True) -> bool:
    """Render a collapsible section header.

    Args:
        label: Section title.
        default_open: Whether the section starts expanded.

    Returns:
        ``True`` if the section is currently expanded.

    Example::

        if ui.collapsing_header("Physics Parameters"):
            ui.drag_float("Mass", ...)
    """
    if not _check_imgui():
        return True
    flags = imgui.TREE_NODE_DEFAULT_OPEN if default_open else 0
    return imgui.collapsing_header(label, flags=flags)


def tooltip(text_str: str) -> None:
    """Show a tooltip when the previous widget is hovered.

    Args:
        text_str: Tooltip text.

    Example::

        ui.drag_float("Mass", ...)
        ui.tooltip("Mass of the link in kilograms")
    """
    if not _check_imgui():
        return
    if imgui.is_item_hovered():
        imgui.begin_tooltip()
        imgui.text(text_str)
        imgui.end_tooltip()
