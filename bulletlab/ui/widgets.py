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

from typing import Any, Callable

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
    highlight: bool = False,
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
    
    if highlight:
        imgui.push_style_color(imgui.COLOR_SLIDER_GRAB, 0.9, 0.2, 0.2, 1.0)
        imgui.push_style_color(imgui.COLOR_SLIDER_GRAB_ACTIVE, 1.0, 0.3, 0.3, 1.0)
        
    changed, new_val = imgui.slider_float(label, current, min_val, max_val, fmt)
    
    if highlight:
        imgui.pop_style_color(2)
        
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


# ------------------------------------------------------------------
# Toggle Switch widget
# ------------------------------------------------------------------

def toggle_switch(
    label: str,
    getter: "Callable[[], bool] | bool",
    setter: "Callable[[bool], None] | None" = None,
    color_on:  "tuple[float, float, float, float]" = (0.2, 0.75, 1.0, 1.0),
    color_off: "tuple[float, float, float, float]" = (0.3, 0.3, 0.3, 1.0),
    width: int = 44,
    height: int = 22,
) -> bool:
    """Render a capsule-shaped toggle switch with a sliding handle.

    The capsule is **grayed out** when ``False`` and **lit up** in ``color_on``
    when ``True``.  The inner circle glides between the left and right sides.
    A text label is rendered to the right of the switch.

    Follows the same getter / setter pattern as all other BulletLab widgets,
    so state can live in any Python variable.

    Args:
        label:     Text label shown to the right of the switch.
        getter:    Current state (``bool``) or a callable that returns it.
        setter:    Called with the new state when clicked.
        color_on:  RGBA color of the capsule when the switch is ``True``.
        color_off: RGBA color of the capsule when the switch is ``False``.
        width:     Total width of the capsule in pixels.
        height:    Height of the capsule in pixels (also the diameter of the handle).

    Returns:
        Current state (``True`` / ``False``) after this frame.

    Example::

        # Simple one-liner — state lives in a list cell
        ui.toggle_switch("Autopilot", lambda: autopilot_on[0],
                         setter=lambda v: autopilot_on.__setitem__(0, v))

        # Or compose it yourself
        toggled = ui.toggle_switch("Motors", lambda: motors_on)
        if toggled != motors_on:
            motors_on = toggled
            apply_motors(motors_on)
    """
    if not _check_imgui():
        return bool(getter() if callable(getter) else getter)

    current = bool(getter() if callable(getter) else getter)

    # ── Geometry ─────────────────────────────────────────────────────────────
    radius   = height / 2.0
    handle_r = radius - 2.0
    padding  = 2.0

    # ── Invisible hit-box (covers just the capsule) ───────────────────────────
    cursor_x, cursor_y = imgui.get_cursor_screen_pos()
    imgui.invisible_button(f"##tgsw_{label}", float(width), float(height))
    clicked = imgui.is_item_clicked(0)

    new_val = current
    if clicked:
        new_val = not current
        if setter is not None:
            setter(new_val)

    # ── Draw capsule background ───────────────────────────────────────────────
    draw = imgui.get_window_draw_list()

    bg_r, bg_g, bg_b, bg_a = color_on if new_val else color_off
    # Darken slightly when off to look naturally inactive
    if not new_val:
        bg_r, bg_g, bg_b = bg_r * 0.8, bg_g * 0.8, bg_b * 0.8

    bg_col = imgui.get_color_u32_rgba(bg_r, bg_g, bg_b, bg_a)
    x0 = cursor_x
    y0 = cursor_y
    x1 = cursor_x + width
    y1 = cursor_y + height
    draw.add_rect_filled(x0, y0, x1, y1, bg_col, radius)

    # Subtle border
    border_alpha = 0.6 if new_val else 0.3
    border_col = imgui.get_color_u32_rgba(1.0, 1.0, 1.0, border_alpha)
    draw.add_rect(x0, y0, x1, y1, border_col, radius, 0, 1.0)

    # ── Draw sliding circle ───────────────────────────────────────────────────
    handle_x = (cursor_x + width - radius - padding) if new_val \
               else (cursor_x + radius + padding)
    handle_y = cursor_y + radius
    handle_col = imgui.get_color_u32_rgba(1.0, 1.0, 1.0, 1.0)
    shadow_col = imgui.get_color_u32_rgba(0.0, 0.0, 0.0, 0.25)
    # Tiny shadow
    draw.add_circle_filled(handle_x + 1, handle_y + 1, handle_r, shadow_col, 20)
    draw.add_circle_filled(handle_x, handle_y, handle_r, handle_col, 20)

    # ── Label to the right ────────────────────────────────────────────────────
    imgui.same_line()
    imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() + (height - imgui.get_font_size()) * 0.5)
    imgui.text(label)

    return new_val


# ------------------------------------------------------------------
# Joystick widget
# ------------------------------------------------------------------

# Per-joystick persistent state: maps label -> [handle_x, handle_y] in pixels,
# relative to joystick center.  Stored here because ImGui is stateless between
# frames (immediate-mode).
_joystick_state: dict[str, list[float]] = {}


def joystick(
    label: str,
    on_x: "Callable[[float], None] | None" = None,
    on_y: "Callable[[float], None] | None" = None,
    snap: bool = True,
    size: int = 60,
    handle_color: "tuple[float, float, float, float]" = (0.2, 0.6, 1.0, 1.0),
) -> "tuple[float, float]":
    """Render an interactive 2D virtual joystick inside any custom panel.

    The joystick consists of a fixed outer ring and a smaller draggable
    handle.  Both axes are reported as floats in ``[-1.0, 1.0]`` and the
    callbacks ``on_x`` / ``on_y`` are called **every frame** so that
    continuous commands (e.g. wheel velocities) keep firing even when the
    handle is held still.

    Args:
        label:        Unique name for this joystick. Displayed as a label
                      above the widget.  Must be unique per panel if you
                      have more than one joystick.
        on_x:         Callback receiving the X axis value in ``[-1, 1]``.
                      Positive X → right.  Pass ``None`` to ignore X.
        on_y:         Callback receiving the Y axis value in ``[-1, 1]``.
                      Positive Y → **up** (handle dragged toward top of
                      screen), which is the natural "forward" direction
                      for a drive joystick.  Pass ``None`` to ignore Y.
        snap:         If ``True`` (default) the handle jumps back to center
                      when the mouse is released — the robot stops when you
                      let go.  If ``False`` the handle stays where it was
                      dropped and keeps sending that command until you move
                      it again (latching / cruise mode).
        size:         Radius of the outer ring in pixels.  The handle radius
                      is ``size // 3``.
        handle_color: RGBA color of the draggable handle as four floats in
                      ``[0, 1]``.  Defaults to a vivid blue.

    Returns:
        ``(x, y)`` — the current normalized axis values ``[-1, 1]``.

    Examples::

        # Differential drive rover — Y drives forward, X turns
        @app.custom_panel("Drive")
        def drive_panel():
            ui.joystick(
                "Rover Drive",
                on_x=lambda v: [setattr(robot.joints["wheel_left"],  "velocity", (-v) * 10),
                                 setattr(robot.joints["wheel_right"], "velocity",   v  * 10)],
                on_y=lambda v: [setattr(robot.joints["wheel_left"],  "velocity", v * 10),
                                setattr(robot.joints["wheel_right"], "velocity", v * 10)],
            )

        # Two independent joysticks in the same panel
        @app.custom_panel("Arm Control")
        def arm_panel():
            ui.joystick("Shoulder", on_y=lambda v: setattr(robot.joints["shoulder"], "velocity", v * 5))
            ui.same_line()
            ui.joystick("Elbow",    on_y=lambda v: setattr(robot.joints["elbow"],    "velocity", v * 5),
                        handle_color=(1.0, 0.5, 0.1, 1.0))

        # Latching joystick — keeps driving after you release
        @app.custom_panel("Cruise")
        def cruise_panel():
            ui.joystick("Cruise Drive", on_y=lambda v: setattr(robot.joints["drive"], "velocity", v * 8),
                        snap=False, handle_color=(0.2, 0.9, 0.4, 1.0))
    """
    if not _check_imgui():
        return (0.0, 0.0)

    # ── Initialise per-joystick state ────────────────────────────────────────
    if label not in _joystick_state:
        _joystick_state[label] = [0.0, 0.0]   # [handle_x_px, handle_y_px]
    state = _joystick_state[label]

    handle_r = max(8, size // 3)

    # ── Draw label ───────────────────────────────────────────────────────────
    imgui.text(label)

    # ── Invisible interaction button (full bounding box) ─────────────────────
    btn_size = (size * 2 + 4, size * 2 + 4)
    cursor_x, cursor_y = imgui.get_cursor_screen_pos()
    imgui.invisible_button(f"##jstk_{label}", btn_size[0], btn_size[1])

    is_active  = imgui.is_item_active()
    is_hovered = imgui.is_item_hovered()

    center_x = cursor_x + size + 2
    center_y = cursor_y + size + 2

    # ── Handle drag ──────────────────────────────────────────────────────────
    if is_active:
        io = imgui.get_io()
        dx = io.mouse_delta[0]
        dy = io.mouse_delta[1]
        state[0] += dx
        state[1] += dy
        # Constrain handle to stay within the outer ring
        dist = (state[0] ** 2 + state[1] ** 2) ** 0.5
        max_r = float(size - handle_r)
        if dist > max_r and dist > 0:
            scale = max_r / dist
            state[0] *= scale
            state[1] *= scale
    elif snap:
        # Smooth snap-back: lerp toward center (instant for now, looks fine)
        state[0] = 0.0
        state[1] = 0.0

    # ── Normalise to [-1, 1] ─────────────────────────────────────────────────
    max_r = float(size - handle_r)
    norm_x =  state[0] / max_r if max_r > 0 else 0.0
    norm_y = -state[1] / max_r if max_r > 0 else 0.0  # flip Y: up = positive

    norm_x = max(-1.0, min(1.0, norm_x))
    norm_y = max(-1.0, min(1.0, norm_y))

    # ── Fire callbacks every frame ───────────────────────────────────────────
    if on_x is not None:
        on_x(norm_x)
    if on_y is not None:
        on_y(norm_y)

    # ── Draw ─────────────────────────────────────────────────────────────────
    draw = imgui.get_window_draw_list()

    # Outer ring background
    ring_bg_col = imgui.get_color_u32_rgba(0.15, 0.15, 0.15, 0.85) if not is_hovered \
                  else imgui.get_color_u32_rgba(0.2,  0.2,  0.2,  0.9)
    draw.add_circle_filled(center_x, center_y, float(size), ring_bg_col, 64)

    # Outer ring border
    border_col = imgui.get_color_u32_rgba(0.5, 0.5, 0.5, 0.7) if not is_active \
                 else imgui.get_color_u32_rgba(0.8, 0.8, 0.8, 1.0)
    draw.add_circle(center_x, center_y, float(size), border_col, 64, 2.0)

    # Cross-hair lines (subtle guide)
    guide_col = imgui.get_color_u32_rgba(0.4, 0.4, 0.4, 0.4)
    draw.add_line(center_x - size + 4, center_y, center_x + size - 4, center_y, guide_col, 1.0)
    draw.add_line(center_x, center_y - size + 4, center_x, center_y + size - 4, guide_col, 1.0)

    # Handle
    hx = center_x + state[0]
    hy = center_y + state[1]
    r, g, b, a = handle_color
    h_col      = imgui.get_color_u32_rgba(r, g, b, a)
    h_col_dark = imgui.get_color_u32_rgba(r * 0.6, g * 0.6, b * 0.6, a)
    draw.add_circle_filled(hx, hy, float(handle_r), h_col, 32)
    draw.add_circle(hx, hy, float(handle_r), h_col_dark, 32, 1.5)

    return (norm_x, norm_y)

