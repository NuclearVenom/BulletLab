"""
imgui-bundle compatibility shim for BulletLab.

This module provides a drop-in compatibility layer so that existing code
written against the ``imgui-bundle`` library.
unchanged while the backend has been switched to ``imgui-bundle``.

Internal API wrapper mapping BulletLab UI calls to `imgui-bundle`.

All wrappers delegate to ``imgui_bundle.imgui``. They are intentionally
small — no business logic, no feature additions.
"""

from __future__ import annotations

import types
from typing import Any, Optional, Tuple

from imgui_bundle import imgui as _imgui

# ---------------------------------------------------------------------------
# ImVec2 / ImVec4 — needed by wrappers below
# ---------------------------------------------------------------------------
ImVec2 = _imgui.ImVec2
ImVec4 = _imgui.ImVec4

# ===========================================================================
# Colour constants
#
# Not every imgui-bundle build exposes every Col_ member — the set depends on
# which Dear ImGui version was compiled in.  Use _col() to safely retrieve a
# value and fall back to 0 when the attribute is absent.
# ===========================================================================

def _col(*names: str) -> int:
    """Return the integer value of the first Col_ attribute that exists."""
    for name in names:
        try:
            return getattr(_imgui.Col_, name).value
        except AttributeError:
            continue
    return 0  # safe fallback — won't crash; may show wrong colour

COLOR_TEXT                        = _col("text")
COLOR_TEXT_DISABLED               = _col("text_disabled")
COLOR_WINDOW_BACKGROUND           = _col("window_bg")
COLOR_CHILD_BACKGROUND            = _col("child_bg")
COLOR_POPUP_BACKGROUND            = _col("popup_bg")
COLOR_BORDER                      = _col("border")
COLOR_BORDER_SHADOW               = _col("border_shadow")
COLOR_FRAME_BACKGROUND            = _col("frame_bg")
COLOR_FRAME_BACKGROUND_HOVERED    = _col("frame_bg_hovered")
COLOR_FRAME_BACKGROUND_ACTIVE     = _col("frame_bg_active")
COLOR_TITLE_BACKGROUND            = _col("title_bg")
COLOR_TITLE_BACKGROUND_ACTIVE     = _col("title_bg_active")
COLOR_TITLE_BACKGROUND_COLLAPSED  = _col("title_bg_collapsed")
COLOR_MENUBAR_BACKGROUND          = _col("menu_bar_bg")
COLOR_SCROLLBAR_BACKGROUND        = _col("scrollbar_bg")
COLOR_SCROLLBAR_GRAB              = _col("scrollbar_grab")
COLOR_SCROLLBAR_GRAB_HOVERED      = _col("scrollbar_grab_hovered")
COLOR_SCROLLBAR_GRAB_ACTIVE       = _col("scrollbar_grab_active")
COLOR_CHECK_MARK                  = _col("check_mark")
COLOR_SLIDER_GRAB                 = _col("slider_grab")
COLOR_SLIDER_GRAB_ACTIVE          = _col("slider_grab_active")
COLOR_BUTTON                      = _col("button")
COLOR_BUTTON_HOVERED              = _col("button_hovered")
COLOR_BUTTON_ACTIVE               = _col("button_active")
COLOR_HEADER                      = _col("header")
COLOR_HEADER_HOVERED              = _col("header_hovered")
COLOR_HEADER_ACTIVE               = _col("header_active")
COLOR_SEPARATOR                   = _col("separator")
COLOR_SEPARATOR_HOVERED           = _col("separator_hovered")
COLOR_SEPARATOR_ACTIVE            = _col("separator_active")
COLOR_RESIZE_GRIP                 = _col("resize_grip")
COLOR_RESIZE_GRIP_HOVERED         = _col("resize_grip_hovered")
COLOR_RESIZE_GRIP_ACTIVE          = _col("resize_grip_active")
# Tab colours — added in ImGui 1.72; fall back gracefully on older builds
COLOR_TAB                         = _col("tab", "tab_normal")
COLOR_TAB_HOVERED                 = _col("tab_hovered")
COLOR_TAB_ACTIVE                  = _col("tab_active", "tab_selected")
COLOR_TAB_UNFOCUSED               = _col("tab_unfocused", "tab_dimmed")
COLOR_TAB_UNFOCUSED_ACTIVE        = _col("tab_unfocused_active", "tab_dimmed_selected")
COLOR_PLOT_LINES                  = _col("plot_lines")
COLOR_PLOT_LINES_HOVERED          = _col("plot_lines_hovered")
COLOR_PLOT_HISTOGRAM              = _col("plot_histogram")
COLOR_PLOT_HISTOGRAM_HOVERED      = _col("plot_histogram_hovered")
# Table colours — added in ImGui 1.80
COLOR_TABLE_HEADER_BACKGROUND     = _col("table_header_bg")
COLOR_TABLE_BORDER_STRONG         = _col("table_border_strong")
COLOR_TABLE_BORDER_LIGHT          = _col("table_border_light")
COLOR_TABLE_ROW_BACKGROUND        = _col("table_row_bg")
COLOR_TABLE_ROW_BACKGROUND_ALT    = _col("table_row_bg_alt")
COLOR_TEXT_SELECTED_BACKGROUND    = _col("text_selected_bg")
COLOR_DRAG_DROP_TARGET            = _col("drag_drop_target")
COLOR_NAV_HIGHLIGHT               = _col("nav_highlight", "nav_cursor")  # renamed nav_cursor in 1.92.x
COLOR_NAV_WINDOWING_HIGHLIGHT     = _col("nav_windowing_highlight")
COLOR_NAV_WINDOWING_DIM_BACKGROUND= _col("nav_windowing_dim_bg")
COLOR_MODAL_WINDOW_DIM_BACKGROUND = _col("modal_window_dim_bg")

# ===========================================================================
# Window / TreeNode / InputText / Selectable flags
# WindowFlags
# Use safe helpers — enum member names vary across imgui-bundle versions.
# ===========================================================================

def _wf(*names: str) -> int:
    for n in names:
        try:
            return getattr(_imgui.WindowFlags_, n).value
        except AttributeError:
            continue
    return 0

def _tn(*names: str) -> int:
    for n in names:
        try:
            return getattr(_imgui.TreeNodeFlags_, n).value
        except AttributeError:
            continue
    return 0

def _it(*names: str) -> int:
    for n in names:
        try:
            return getattr(_imgui.InputTextFlags_, n).value
        except AttributeError:
            continue
    return 0

def _sel(*names: str) -> int:
    for n in names:
        try:
            return getattr(_imgui.SelectableFlags_, n).value
        except AttributeError:
            continue
    return 0

WINDOW_NO_TITLE_BAR               = _wf("no_title_bar")
WINDOW_NO_RESIZE                  = _wf("no_resize")
WINDOW_NO_MOVE                    = _wf("no_move")
WINDOW_NO_SCROLLBAR               = _wf("no_scrollbar")
WINDOW_NO_SCROLL_WITH_MOUSE       = _wf("no_scroll_with_mouse")
WINDOW_NO_COLLAPSE                = _wf("no_collapse")
WINDOW_ALWAYS_AUTO_RESIZE         = _wf("always_auto_resize")
WINDOW_NO_BACKGROUND              = _wf("no_background")
WINDOW_NO_SAVED_SETTINGS          = _wf("no_saved_settings")
WINDOW_NO_MOUSE_INPUTS            = _wf("no_mouse_inputs")
WINDOW_MENU_BAR                   = _wf("menu_bar")
WINDOW_HORIZONTAL_SCROLLING_BAR   = _wf("horizontal_scrollbar")
WINDOW_NO_FOCUS_ON_APPEARING      = _wf("no_focus_on_appearing")
WINDOW_NO_BRING_TO_DISPLAY_FRONT  = _wf("no_bring_to_display_front")
WINDOW_ALWAYS_VERTICAL_SCROLLBAR  = _wf("always_vertical_scrollbar")
WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR= _wf("always_horizontal_scrollbar")

TREE_NODE_DEFAULT_OPEN            = _tn("default_open")
TREE_NODE_OPEN_ON_DOUBLE_CLICK    = _tn("open_on_double_click")
TREE_NODE_OPEN_ON_ARROW           = _tn("open_on_arrow")
TREE_NODE_LEAF                    = _tn("leaf")
TREE_NODE_BULLET                  = _tn("bullet")
TREE_NODE_FRAMED                  = _tn("framed")
TREE_NODE_NO_TREE_PUSH_ON_OPEN    = _tn("no_tree_push_on_open")
TREE_NODE_SPAN_AVAILABLE_WIDTH    = _tn("span_avail_width")
TREE_NODE_SPAN_FULL_WIDTH         = _tn("span_full_width")
TREE_NODE_SELECTED                = _tn("selected")

INPUT_TEXT_ENTER_RETURNS_TRUE     = _it("enter_returns_true")
INPUT_TEXT_CALLBACK_ALWAYS        = _it("callback_always")
INPUT_TEXT_AUTO_SELECT_ALL        = _it("auto_select_all")
INPUT_TEXT_CHARS_DECIMAL          = _it("chars_decimal")
INPUT_TEXT_CHARS_HEXADECIMAL      = _it("chars_hexadecimal")
INPUT_TEXT_READ_ONLY              = _it("read_only")
INPUT_TEXT_PASSWORD               = _it("password")
INPUT_TEXT_NO_UNDO_REDO           = _it("no_undo_redo")
INPUT_TEXT_ALLOW_TAB_INPUT        = _it("allow_tab_input")
INPUT_TEXT_NO_BORDER              = _it("no_border")   # 0 if not present (imgui < 1.90)
INPUT_TEXT_MULTILINE              = 0  # sentinel; handled by input_text_multiline()

SELECTABLE_SPAN_ALL_COLUMNS       = _sel("span_all_columns")
SELECTABLE_ALLOW_DOUBLE_CLICK     = _sel("allow_double_click")

# ===========================================================================
# StyleVar constants
# ===========================================================================

def _sv(*names: str) -> int:
    for n in names:
        try:
            return getattr(_imgui.StyleVar_, n).value
        except AttributeError:
            continue
    return 0

STYLE_ALPHA                       = _sv("alpha")
STYLE_DISABLED_ALPHA              = _sv("disabled_alpha")
STYLE_WINDOW_PADDING              = _sv("window_padding")
STYLE_WINDOW_ROUNDING             = _sv("window_rounding")
STYLE_WINDOW_BORDER_SIZE          = _sv("window_border_size")
STYLE_WINDOW_MIN_SIZE             = _sv("window_min_size")
STYLE_WINDOW_TITLE_ALIGN          = _sv("window_title_align")
STYLE_CHILD_ROUNDING              = _sv("child_rounding")
STYLE_CHILD_BORDER_SIZE           = _sv("child_border_size")
STYLE_POPUP_ROUNDING              = _sv("popup_rounding")
STYLE_POPUP_BORDER_SIZE           = _sv("popup_border_size")
STYLE_FRAME_PADDING               = _sv("frame_padding")
STYLE_FRAME_ROUNDING              = _sv("frame_rounding")
STYLE_FRAME_BORDER_SIZE           = _sv("frame_border_size")
STYLE_ITEM_SPACING                = _sv("item_spacing")
STYLE_ITEM_INNER_SPACING          = _sv("item_inner_spacing")
STYLE_INDENT_SPACING              = _sv("indent_spacing")
STYLE_CELL_PADDING                = _sv("cell_padding")
STYLE_SCROLLBAR_SIZE              = _sv("scrollbar_size")
STYLE_SCROLLBAR_ROUNDING          = _sv("scrollbar_rounding")
STYLE_GRAB_MIN_SIZE               = _sv("grab_min_size")
STYLE_GRAB_ROUNDING               = _sv("grab_rounding")
STYLE_TAB_ROUNDING                = _sv("tab_rounding")
STYLE_BUTTON_TEXT_ALIGN           = _sv("button_text_align")
STYLE_SELECTABLE_TEXT_ALIGN       = _sv("selectable_text_align")

# ===========================================================================
# Signature-change wrapper functions
# ===========================================================================

def set_next_window_position(x: float, y: float, condition: int = 0) -> None:
    """set_next_window_position(x, y, condition=0)"""
    _imgui.set_next_window_pos(ImVec2(x, y), condition)


def set_next_window_size(width: float, height: float, condition: int = 0) -> None:
    """set_next_window_size(width, height, condition=0)"""
    _imgui.set_next_window_size(ImVec2(width, height), condition)


def begin(
    label: str,
    closable: bool = False,
    flags: int = 0,
) -> Tuple[bool, bool]:
    """begin(label, closable=False, flags=0) -> (expanded, opened)"""
    if closable:
        visible, p_open = _imgui.begin(label, True, flags)
        return visible, bool(p_open)
    else:
        visible, _ = _imgui.begin(label, None, flags)
        return visible, True


def end() -> None:
    _imgui.end()


def collapsing_header(
    label: str, closable: bool = False, flags: int = 0
) -> Tuple[bool, bool]:
    """collapsing_header(label, closable=False, flags=0) -> (expanded, visible)"""
    if closable:
        result = _imgui.collapsing_header(label, True, flags)
        return bool(result[0]), bool(result[1])
    else:
        result = _imgui.collapsing_header(label, flags)
        expanded = bool(result) if not isinstance(result, tuple) else bool(result[0])
        return expanded, True


def text_colored(text: str, r: float, g: float, b: float, a: float = 1.0) -> None:
    """text_colored(text, r, g, b, a=1.0)"""
    _imgui.text_colored(ImVec4(r, g, b, a), text)


def push_style_color(idx: int, r: float, g: float, b: float, a: float = 1.0) -> None:
    """push_style_color(idx, r, g, b, a=1.0)"""
    _imgui.push_style_color(idx, ImVec4(r, g, b, a))


def pop_style_color(count: int = 1) -> None:
    _imgui.pop_style_color(count)


def same_line(position: float = 0.0, spacing: float = -1.0) -> None:
    """same_line(position=0.0, spacing=-1.0)"""
    _imgui.same_line(position, spacing)


def menu_item(
    label: str,
    shortcut: Optional[str] = None,
    selected: bool = False,
    enabled: bool = True,
) -> Tuple[bool, bool]:
    """menu_item(label, shortcut=None, selected=False, enabled=True) -> (clicked, state)"""
    shortcut = shortcut or ""
    result = _imgui.menu_item(label, shortcut, selected, enabled)
    return bool(result[0]), bool(result[1])


def checkbox(label: str, state: bool) -> Tuple[bool, bool]:
    result = _imgui.checkbox(label, state)
    return bool(result[0]), bool(result[1])


def slider_float(
    label: str,
    value: float,
    min_value: float,
    max_value: float,
    format: str = "%.3f",
    power: float = 1.0,
) -> Tuple[bool, float]:
    """slider_float(label, value, min, max, format=…, power=1.0) -> (changed, value)"""
    result = _imgui.slider_float(label, value, min_value, max_value, format)
    return bool(result[0]), float(result[1])


def input_text(
    label: str,
    value: str,
    buffer_length: int = 255,
    flags: int = 0,
) -> Tuple[bool, str]:
    """input_text(label, value, buffer_length=255, flags=0) -> (changed, str)"""
    result = _imgui.input_text(label, value, flags)
    return bool(result[0]), str(result[1])


def input_text_multiline(
    label: str,
    value: str,
    buffer_length: int = 255,
    width: float = 0.0,
    height: float = 0.0,
    flags: int = 0,
) -> Tuple[bool, str]:
    """input_text_multiline(label, value, buffer_length, width, height, flags)"""
    result = _imgui.input_text_multiline(label, value, ImVec2(width, height), flags)
    return bool(result[0]), str(result[1])


def get_style() -> Any:
    """Return a style proxy wrapping imgui_bundle's style."""
    return _StyleProxy(_imgui.get_style())


# ===========================================================================
# Geometry / IO wrappers — return plain tuples so [0] / [1] indexing works
# ===========================================================================

def get_content_region_available() -> Tuple[float, float]:
    """returns (w, h) tuple."""
    v = _imgui.get_content_region_avail()
    return (float(v.x), float(v.y))


def get_cursor_pos() -> Tuple[float, float]:
    v = _imgui.get_cursor_pos()
    return (float(v.x), float(v.y))


def get_cursor_screen_pos() -> Tuple[float, float]:
    v = _imgui.get_cursor_screen_pos()
    return (float(v.x), float(v.y))


def get_window_content_region_max() -> Tuple[float, float]:
    try:
        v = _imgui.get_window_content_region_max()
        return (float(v.x), float(v.y))
    except AttributeError:
        pass
        
    try:
        v = _imgui.get_content_region_max()
        return (float(v.x), float(v.y))
    except AttributeError:
        pass
        
    # ImGui 1.90+ removed these. The equivalent max coordinate 
    # relative to the window can be calculated as:
    pos = _imgui.get_cursor_pos()
    avail = _imgui.get_content_region_avail()
    return (float(pos.x + avail.x), float(pos.y + avail.y))


# ===========================================================================
# Widget wrappers
# ===========================================================================

def button(label: str, width: float = 0.0, height: float = 0.0) -> bool:
    """button(label, width=0, height=0) -> bool"""
    return bool(_imgui.button(label, ImVec2(width, height)))


def begin_child(
    str_id: str,
    width: float = 0.0,
    height: float = 0.0,
    border: bool = False,
    flags: int = 0,
) -> bool:
    """begin_child(id, width=0, height=0, border=False, flags=0)"""
    if border:
        # Try modern imgui-bundle ChildFlags_ (name varies by version)
        try:
            child_flags = _imgui.ChildFlags_.border.value
        except AttributeError:
            try:
                child_flags = _imgui.ChildFlags_.borders.value
            except AttributeError:
                child_flags = 1  # ImGuiChildFlags_Border raw value
    else:
        child_flags = 0
    return bool(_imgui.begin_child(str_id, ImVec2(width, height), child_flags, flags))


def dummy(width: float, height: float) -> None:
    """dummy(width, height)"""
    _imgui.dummy(ImVec2(width, height))


def get_color_u32_rgba(r: float, g: float, b: float, a: float) -> int:
    """get_color_u32_rgba(r, g, b, a)"""
    return _imgui.get_color_u32(ImVec4(r, g, b, a))


# ===========================================================================
# IO wrapper — wrap mouse_delta so [0]/[1] indexing works
# ===========================================================================

class _IoProxy:
    """Wraps imgui IO so that ImVec2 fields work with [0]/[1] indexing."""

    def __init__(self, io: Any) -> None:
        object.__setattr__(self, '_io', io)

    def __getattr__(self, name: str) -> Any:
        val = getattr(object.__getattribute__(self, '_io'), name)
        # Wrap ImVec2 fields so tuple-indexing works.
        if hasattr(val, 'x') and hasattr(val, 'y') and not isinstance(val, (float, int)):
            return (float(val.x), float(val.y))
        return val

    def __setattr__(self, name: str, value: Any) -> None:
        if name == '_io':
            object.__setattr__(self, name, value)
        else:
            setattr(object.__getattribute__(self, '_io'), name, value)


def get_io() -> Any:
    return _IoProxy(_imgui.get_io())


# ===========================================================================
# DrawList proxy — wrap add_circle_filled so it accepts positional x, y args
# ===========================================================================

class _DrawListProxy:
    """Wraps ImDrawList so positional args (x, y, ...) work.

    style: draw.add_*(x0, y0, x1, y1, col, ...)
    imgui-bundle: draw.add_*(ImVec2(x0,y0), ImVec2(x1,y1), col, ...)
    """

    def __init__(self, dl: Any) -> None:
        self._dl = dl

    def add_circle_filled(
        self,
        x_or_center: Any,
        y_or_radius: float,
        radius_or_col: Any,
        col_or_segments: Any = None,
        num_segments: int = 0,
    ) -> None:
        if col_or_segments is not None:
            # style: (x, y, radius, col, segments=0)
            self._dl.add_circle_filled(
                ImVec2(float(x_or_center), float(y_or_radius)),
                float(radius_or_col),
                col_or_segments,
                num_segments,
            )
        else:
            self._dl.add_circle_filled(x_or_center, y_or_radius, radius_or_col)

    def add_circle(
        self,
        x_or_center: Any,
        y_or_radius: float,
        radius_or_col: Any,
        col_or_segments: Any = None,
        num_segments: int = 0,
        thickness: float = 1.0,
    ) -> None:
        if col_or_segments is not None:
            self._dl.add_circle(
                ImVec2(float(x_or_center), float(y_or_radius)),
                float(radius_or_col),
                col_or_segments,
                num_segments,
                thickness,
            )
        else:
            self._dl.add_circle(x_or_center, y_or_radius, radius_or_col)

    def add_rect_filled(
        self,
        x0: float, y0: float,
        x1: float, y1: float,
        col: Any,
        rounding: float = 0.0,
        flags: int = 0,
    ) -> None:
        self._dl.add_rect_filled(
            ImVec2(float(x0), float(y0)),
            ImVec2(float(x1), float(y1)),
            col,
            rounding,
            flags,
        )

    def add_rect(
        self,
        x0: float, y0: float,
        x1: float, y1: float,
        col: Any,
        rounding: float = 0.0,
        flags: int = 0,
        thickness: float = 1.0,
    ) -> None:
        self._dl.add_rect(
            ImVec2(float(x0), float(y0)),
            ImVec2(float(x1), float(y1)),
            col,
            rounding,
            thickness,
            flags,
        )

    def add_line(
        self,
        x0: float, y0: float,
        x1: float, y1: float,
        col: Any,
        thickness: float = 1.0,
    ) -> None:
        self._dl.add_line(
            ImVec2(float(x0), float(y0)),
            ImVec2(float(x1), float(y1)),
            col,
            thickness,
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._dl, name)


def get_window_draw_list() -> _DrawListProxy:
    return _DrawListProxy(_imgui.get_window_draw_list())


# ===========================================================================
# Additional widget wrappers
# ===========================================================================

def invisible_button(str_id: str, width: float, height: float = 0.0, flags: int = 0) -> bool:
    """invisible_button(id, width, height)"""
    return bool(_imgui.invisible_button(str_id, ImVec2(float(width), float(height)), flags))


def color_edit3(label: str, r: float, g: float, b: float, flags: int = 0) -> Tuple[bool, Tuple[float, float, float]]:
    """color_edit3(label, r, g, b) → (changed, (r, g, b))."""
    result = _imgui.color_edit3(label, (r, g, b), flags)
    changed = bool(result[0])
    col = result[1]  # ImVec4 or tuple
    if hasattr(col, 'x'):
        return changed, (float(col.x), float(col.y), float(col.z))
    return changed, (float(col[0]), float(col[1]), float(col[2]))


def input_float(
    label: str,
    value: float,
    step: float = 0.0,
    step_fast: float = 0.0,
    format: str = "%.3f",
    flags: int = 0,
) -> Tuple[bool, float]:
    """input_float(label, value, step=0, step_fast=0, format=…) → (changed, float)."""
    result = _imgui.input_float(label, value, step, step_fast, format, flags)
    return bool(result[0]), float(result[1])


def get_cursor_pos_y() -> float:
    return float(_imgui.get_cursor_pos_y())


def set_cursor_pos_y(y: float) -> None:
    _imgui.set_cursor_pos_y(float(y))


def get_font_size() -> float:
    return float(_imgui.get_font_size())




# ===========================================================================
# Style proxy helpers
# ===========================================================================

class _StyleColorsProxy:
    """Proxy for style.colors that accepts 4-tuples as values."""

    def __init__(self, style: Any) -> None:
        self._style = style

    def __setitem__(self, idx: int, rgba: Any) -> None:
        if isinstance(rgba, (tuple, list)) and len(rgba) == 4:
            self._style.colors[idx] = ImVec4(rgba[0], rgba[1], rgba[2], rgba[3])
        else:
            self._style.colors[idx] = rgba

    def __getitem__(self, idx: int) -> Any:
        return self._style.colors[idx]


class _StyleProxy:
    """Proxy for imgui Style that makes style.colors accept 4-tuples."""

    def __init__(self, style: Any) -> None:
        object.__setattr__(self, '_style', style)
        object.__setattr__(self, 'colors', _StyleColorsProxy(style))

    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, '_style'), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ('_style', 'colors'):
            object.__setattr__(self, name, value)
        else:
            setattr(object.__getattribute__(self, '_style'), name, value)


# ===========================================================================
# ``imgui`` PROXY OBJECT
# ===========================================================================
# Panels and widgets do  ``import imgui`` and then call ``imgui.button()``,
# ``imgui.COLOR_SLIDER_GRAB``, ``imgui.push_style_color(idx, r, g, b, a)``,
# etc.  We export a proxy object that:
#   1. Falls back to ``imgui_bundle.imgui`` for every attribute not listed below.
#   2. Overrides constant names (COLOR_*, WINDOW_*, TREE_NODE_*, INPUT_TEXT_*)
#      to return the integer values expected by imgui-bundle.
#   3. Overrides the few functions whose call-signatures differ.
# ===========================================================================

# Collect all constant aliases and wrapper overrides in a single dict.
_COMPAT_ATTRS: dict[str, Any] = {
    # -- Color constants --
    "COLOR_TEXT":                        COLOR_TEXT,
    "COLOR_TEXT_DISABLED":               COLOR_TEXT_DISABLED,
    "COLOR_WINDOW_BACKGROUND":           COLOR_WINDOW_BACKGROUND,
    "COLOR_CHILD_BACKGROUND":            COLOR_CHILD_BACKGROUND,
    "COLOR_POPUP_BACKGROUND":            COLOR_POPUP_BACKGROUND,
    "COLOR_BORDER":                      COLOR_BORDER,
    "COLOR_BORDER_SHADOW":               COLOR_BORDER_SHADOW,
    "COLOR_FRAME_BACKGROUND":            COLOR_FRAME_BACKGROUND,
    "COLOR_FRAME_BACKGROUND_HOVERED":    COLOR_FRAME_BACKGROUND_HOVERED,
    "COLOR_FRAME_BACKGROUND_ACTIVE":     COLOR_FRAME_BACKGROUND_ACTIVE,
    "COLOR_TITLE_BACKGROUND":            COLOR_TITLE_BACKGROUND,
    "COLOR_TITLE_BACKGROUND_ACTIVE":     COLOR_TITLE_BACKGROUND_ACTIVE,
    "COLOR_TITLE_BACKGROUND_COLLAPSED":  COLOR_TITLE_BACKGROUND_COLLAPSED,
    "COLOR_MENUBAR_BACKGROUND":          COLOR_MENUBAR_BACKGROUND,
    "COLOR_SCROLLBAR_BACKGROUND":        COLOR_SCROLLBAR_BACKGROUND,
    "COLOR_SCROLLBAR_GRAB":              COLOR_SCROLLBAR_GRAB,
    "COLOR_SCROLLBAR_GRAB_HOVERED":      COLOR_SCROLLBAR_GRAB_HOVERED,
    "COLOR_SCROLLBAR_GRAB_ACTIVE":       COLOR_SCROLLBAR_GRAB_ACTIVE,
    "COLOR_CHECK_MARK":                  COLOR_CHECK_MARK,
    "COLOR_SLIDER_GRAB":                 COLOR_SLIDER_GRAB,
    "COLOR_SLIDER_GRAB_ACTIVE":          COLOR_SLIDER_GRAB_ACTIVE,
    "COLOR_BUTTON":                      COLOR_BUTTON,
    "COLOR_BUTTON_HOVERED":              COLOR_BUTTON_HOVERED,
    "COLOR_BUTTON_ACTIVE":               COLOR_BUTTON_ACTIVE,
    "COLOR_HEADER":                      COLOR_HEADER,
    "COLOR_HEADER_HOVERED":              COLOR_HEADER_HOVERED,
    "COLOR_HEADER_ACTIVE":               COLOR_HEADER_ACTIVE,
    "COLOR_SEPARATOR":                   COLOR_SEPARATOR,
    "COLOR_SEPARATOR_HOVERED":           COLOR_SEPARATOR_HOVERED,
    "COLOR_SEPARATOR_ACTIVE":            COLOR_SEPARATOR_ACTIVE,
    "COLOR_RESIZE_GRIP":                 COLOR_RESIZE_GRIP,
    "COLOR_RESIZE_GRIP_HOVERED":         COLOR_RESIZE_GRIP_HOVERED,
    "COLOR_RESIZE_GRIP_ACTIVE":          COLOR_RESIZE_GRIP_ACTIVE,
    "COLOR_TAB":                         COLOR_TAB,
    "COLOR_TAB_HOVERED":                 COLOR_TAB_HOVERED,
    "COLOR_TAB_ACTIVE":                  COLOR_TAB_ACTIVE,
    "COLOR_TAB_UNFOCUSED":               COLOR_TAB_UNFOCUSED,
    "COLOR_TAB_UNFOCUSED_ACTIVE":        COLOR_TAB_UNFOCUSED_ACTIVE,
    "COLOR_PLOT_LINES":                  COLOR_PLOT_LINES,
    "COLOR_PLOT_LINES_HOVERED":          COLOR_PLOT_LINES_HOVERED,
    "COLOR_PLOT_HISTOGRAM":              COLOR_PLOT_HISTOGRAM,
    "COLOR_PLOT_HISTOGRAM_HOVERED":      COLOR_PLOT_HISTOGRAM_HOVERED,
    "COLOR_TABLE_HEADER_BACKGROUND":     COLOR_TABLE_HEADER_BACKGROUND,
    "COLOR_TABLE_BORDER_STRONG":         COLOR_TABLE_BORDER_STRONG,
    "COLOR_TABLE_BORDER_LIGHT":          COLOR_TABLE_BORDER_LIGHT,
    "COLOR_TABLE_ROW_BACKGROUND":        COLOR_TABLE_ROW_BACKGROUND,
    "COLOR_TABLE_ROW_BACKGROUND_ALT":    COLOR_TABLE_ROW_BACKGROUND_ALT,
    "COLOR_TEXT_SELECTED_BACKGROUND":    COLOR_TEXT_SELECTED_BACKGROUND,
    "COLOR_DRAG_DROP_TARGET":            COLOR_DRAG_DROP_TARGET,
    "COLOR_NAV_HIGHLIGHT":               COLOR_NAV_HIGHLIGHT,
    "COLOR_NAV_WINDOWING_HIGHLIGHT":     COLOR_NAV_WINDOWING_HIGHLIGHT,
    "COLOR_NAV_WINDOWING_DIM_BACKGROUND":COLOR_NAV_WINDOWING_DIM_BACKGROUND,
    "COLOR_MODAL_WINDOW_DIM_BACKGROUND": COLOR_MODAL_WINDOW_DIM_BACKGROUND,
    # -- Window / TreeNode flags --
    "WINDOW_NO_TITLE_BAR":              WINDOW_NO_TITLE_BAR,
    "WINDOW_NO_RESIZE":                 WINDOW_NO_RESIZE,
    "WINDOW_NO_MOVE":                   WINDOW_NO_MOVE,
    "WINDOW_NO_SCROLLBAR":              WINDOW_NO_SCROLLBAR,
    "WINDOW_NO_SCROLL_WITH_MOUSE":      WINDOW_NO_SCROLL_WITH_MOUSE,
    "WINDOW_NO_COLLAPSE":               WINDOW_NO_COLLAPSE,
    "WINDOW_ALWAYS_AUTO_RESIZE":        WINDOW_ALWAYS_AUTO_RESIZE,
    "WINDOW_NO_BACKGROUND":             WINDOW_NO_BACKGROUND,
    "WINDOW_NO_SAVED_SETTINGS":         WINDOW_NO_SAVED_SETTINGS,
    "WINDOW_NO_MOUSE_INPUTS":           WINDOW_NO_MOUSE_INPUTS,
    "WINDOW_MENU_BAR":                  WINDOW_MENU_BAR,
    "WINDOW_HORIZONTAL_SCROLLING_BAR":  WINDOW_HORIZONTAL_SCROLLING_BAR,
    "WINDOW_NO_FOCUS_ON_APPEARING":     WINDOW_NO_FOCUS_ON_APPEARING,
    "WINDOW_NO_BRING_TO_DISPLAY_FRONT": WINDOW_NO_BRING_TO_DISPLAY_FRONT,
    "WINDOW_ALWAYS_VERTICAL_SCROLLBAR": WINDOW_ALWAYS_VERTICAL_SCROLLBAR,
    "WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR": WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR,
    "TREE_NODE_DEFAULT_OPEN":           TREE_NODE_DEFAULT_OPEN,
    "TREE_NODE_OPEN_ON_DOUBLE_CLICK":   TREE_NODE_OPEN_ON_DOUBLE_CLICK,
    "TREE_NODE_OPEN_ON_ARROW":          TREE_NODE_OPEN_ON_ARROW,
    "TREE_NODE_LEAF":                   TREE_NODE_LEAF,
    "TREE_NODE_BULLET":                 TREE_NODE_BULLET,
    "TREE_NODE_FRAMED":                 TREE_NODE_FRAMED,
    "TREE_NODE_NO_TREE_PUSH_ON_OPEN":   TREE_NODE_NO_TREE_PUSH_ON_OPEN,
    "TREE_NODE_SPAN_AVAILABLE_WIDTH":   TREE_NODE_SPAN_AVAILABLE_WIDTH,
    "TREE_NODE_SPAN_FULL_WIDTH":        TREE_NODE_SPAN_FULL_WIDTH,
    "TREE_NODE_SELECTED":               TREE_NODE_SELECTED,
    # -- InputText flags --
    "INPUT_TEXT_ENTER_RETURNS_TRUE":    INPUT_TEXT_ENTER_RETURNS_TRUE,
    "INPUT_TEXT_CALLBACK_ALWAYS":       INPUT_TEXT_CALLBACK_ALWAYS,
    "INPUT_TEXT_AUTO_SELECT_ALL":       INPUT_TEXT_AUTO_SELECT_ALL,
    "INPUT_TEXT_CHARS_DECIMAL":         INPUT_TEXT_CHARS_DECIMAL,
    "INPUT_TEXT_CHARS_HEXADECIMAL":     INPUT_TEXT_CHARS_HEXADECIMAL,
    "INPUT_TEXT_READ_ONLY":             INPUT_TEXT_READ_ONLY,
    "INPUT_TEXT_PASSWORD":              INPUT_TEXT_PASSWORD,
    "INPUT_TEXT_NO_UNDO_REDO":          INPUT_TEXT_NO_UNDO_REDO,
    "INPUT_TEXT_ALLOW_TAB_INPUT":       INPUT_TEXT_ALLOW_TAB_INPUT,
    "INPUT_TEXT_NO_BORDER":             INPUT_TEXT_NO_BORDER,
    "INPUT_TEXT_MULTILINE":             INPUT_TEXT_MULTILINE,
    # -- Selectable flags --
    "SELECTABLE_SPAN_ALL_COLUMNS":      SELECTABLE_SPAN_ALL_COLUMNS,
    "SELECTABLE_ALLOW_DOUBLE_CLICK":    SELECTABLE_ALLOW_DOUBLE_CLICK,
    # -- Wrapper functions (changed signatures) --
    "set_next_window_position":         set_next_window_position,
    "set_next_window_size":             set_next_window_size,
    "begin":                            begin,
    "end":                              end,
    "collapsing_header":                collapsing_header,
    "text_colored":                     text_colored,
    "push_style_color":                 push_style_color,
    "pop_style_color":                  pop_style_color,
    "same_line":                        same_line,
    "menu_item":                        menu_item,
    "checkbox":                         checkbox,
    "slider_float":                     slider_float,
    "input_text":                       input_text,
    "input_text_multiline":             input_text_multiline,
    "get_style":                        get_style,
    # -- Geometry / IO wrappers --
    "get_content_region_available":     get_content_region_available,
    "get_cursor_pos":                   get_cursor_pos,
    "get_cursor_screen_pos":            get_cursor_screen_pos,
    "get_window_content_region_max":    get_window_content_region_max,
    "get_io":                           get_io,
    "get_window_draw_list":             get_window_draw_list,
    # -- Widget wrappers --
    "button":                           button,
    "begin_child":                      begin_child,
    "dummy":                            dummy,
    "get_color_u32_rgba":               get_color_u32_rgba,
    "plot_lines":                       None,  # will be set after function definition below
}

# plot_lines needs to be defined here (after _COMPAT_ATTRS) to stay organized,
# but we register it into _COMPAT_ATTRS immediately.

def plot_lines(
    label: str,
    values: Any,
    values_offset: int = 0,
    overlay_text: str = "",
    scale_min: float = float("inf"),
    scale_max: float = float("inf"),
    graph_size: Any = None,
) -> None:
    """plot_lines(label, buf, …, graph_size=(w,h)).
    imgui-bundle requires numpy.ndarray[numpy.float32].
    """
    size = ImVec2(0.0, 0.0)
    if graph_size is not None:
        if isinstance(graph_size, (tuple, list)):
            size = ImVec2(float(graph_size[0]), float(graph_size[1]))
        else:
            size = graph_size  # already ImVec2

    # If using imgui-bundle, values needs to be a numpy array.
    try:
        import numpy as np
        import array
        if isinstance(values, (list, array.array)):
            values = np.array(values, dtype=np.float32)
    except ImportError:
        pass

    _imgui.plot_lines(
        label,
        values,
        values_offset,
        overlay_text,
        scale_min,
        scale_max,
        size,
    )

_COMPAT_ATTRS["plot_lines"]        = plot_lines
_COMPAT_ATTRS["invisible_button"]  = invisible_button
_COMPAT_ATTRS["color_edit3"]       = color_edit3
_COMPAT_ATTRS["input_float"]       = input_float
_COMPAT_ATTRS["get_cursor_pos_y"]  = get_cursor_pos_y
_COMPAT_ATTRS["set_cursor_pos_y"]  = set_cursor_pos_y
_COMPAT_ATTRS["get_font_size"]     = get_font_size

def columns(count: int = 1, identifier: str | None = None, border: bool = True) -> None:
    """columns(count=1, id=None, border=True)
    imgui-bundle: columns(count=1, id_=None, borders=True)
    """
    _imgui.columns(count, identifier, border)

_COMPAT_ATTRS["columns"]           = columns

# ---------------------------------------------------------------------------
# push_style_var wrapper
# imgui-bundle accepts the same positional style but value may need ImVec2
# ---------------------------------------------------------------------------

def push_style_var(idx: int, value: Any) -> None:
    """push_style_var(idx, float_or_tuple)."""
    if isinstance(value, (tuple, list)):
        _imgui.push_style_var(idx, ImVec2(float(value[0]), float(value[1])))
    else:
        _imgui.push_style_var(idx, float(value))

_COMPAT_ATTRS["push_style_var"] = push_style_var

# ---------------------------------------------------------------------------
# STYLE_* constants registered so imgui.STYLE_ALPHA etc. work on the proxy
# ---------------------------------------------------------------------------
_COMPAT_ATTRS["STYLE_ALPHA"]                  = STYLE_ALPHA
_COMPAT_ATTRS["STYLE_DISABLED_ALPHA"]         = STYLE_DISABLED_ALPHA
_COMPAT_ATTRS["STYLE_WINDOW_PADDING"]         = STYLE_WINDOW_PADDING
_COMPAT_ATTRS["STYLE_WINDOW_ROUNDING"]        = STYLE_WINDOW_ROUNDING
_COMPAT_ATTRS["STYLE_WINDOW_BORDER_SIZE"]     = STYLE_WINDOW_BORDER_SIZE
_COMPAT_ATTRS["STYLE_WINDOW_MIN_SIZE"]        = STYLE_WINDOW_MIN_SIZE
_COMPAT_ATTRS["STYLE_WINDOW_TITLE_ALIGN"]     = STYLE_WINDOW_TITLE_ALIGN
_COMPAT_ATTRS["STYLE_CHILD_ROUNDING"]         = STYLE_CHILD_ROUNDING
_COMPAT_ATTRS["STYLE_CHILD_BORDER_SIZE"]      = STYLE_CHILD_BORDER_SIZE
_COMPAT_ATTRS["STYLE_POPUP_ROUNDING"]         = STYLE_POPUP_ROUNDING
_COMPAT_ATTRS["STYLE_POPUP_BORDER_SIZE"]      = STYLE_POPUP_BORDER_SIZE
_COMPAT_ATTRS["STYLE_FRAME_PADDING"]          = STYLE_FRAME_PADDING
_COMPAT_ATTRS["STYLE_FRAME_ROUNDING"]         = STYLE_FRAME_ROUNDING
_COMPAT_ATTRS["STYLE_FRAME_BORDER_SIZE"]      = STYLE_FRAME_BORDER_SIZE
_COMPAT_ATTRS["STYLE_ITEM_SPACING"]           = STYLE_ITEM_SPACING
_COMPAT_ATTRS["STYLE_ITEM_INNER_SPACING"]     = STYLE_ITEM_INNER_SPACING
_COMPAT_ATTRS["STYLE_INDENT_SPACING"]         = STYLE_INDENT_SPACING
_COMPAT_ATTRS["STYLE_CELL_PADDING"]           = STYLE_CELL_PADDING
_COMPAT_ATTRS["STYLE_SCROLLBAR_SIZE"]         = STYLE_SCROLLBAR_SIZE
_COMPAT_ATTRS["STYLE_SCROLLBAR_ROUNDING"]     = STYLE_SCROLLBAR_ROUNDING
_COMPAT_ATTRS["STYLE_GRAB_MIN_SIZE"]          = STYLE_GRAB_MIN_SIZE
_COMPAT_ATTRS["STYLE_GRAB_ROUNDING"]          = STYLE_GRAB_ROUNDING
_COMPAT_ATTRS["STYLE_TAB_ROUNDING"]           = STYLE_TAB_ROUNDING
_COMPAT_ATTRS["STYLE_BUTTON_TEXT_ALIGN"]      = STYLE_BUTTON_TEXT_ALIGN
_COMPAT_ATTRS["STYLE_SELECTABLE_TEXT_ALIGN"]  = STYLE_SELECTABLE_TEXT_ALIGN



class _ImguiProxy(types.ModuleType):
    """A module-like proxy around ``imgui_bundle.imgui``.

    Attribute lookup order:
      1. Our compat overrides (_COMPAT_ATTRS) — constants + wrapper fns.
      2. The real ``imgui_bundle.imgui`` module for everything else.

    This lets existing code call ``imgui.button()``, ``imgui.text()``,
    ``imgui.begin_menu()``, etc. unchanged while our overrides intercept
    the constant names and signature-incompatible calls.
    """

    def __init__(self) -> None:
        super().__init__("imgui")
        # Expose the underlying module for callers that need it.
        self._bundle_imgui = _imgui

    def __getattr__(self, name: str) -> Any:
        if name in _COMPAT_ATTRS:
            return _COMPAT_ATTRS[name]
        # Fall through to the real imgui_bundle.imgui module.
        try:
            return getattr(_imgui, name)
        except AttributeError:
            raise AttributeError(
                f"imgui (compat proxy) has no attribute {name!r}. "
                f"If this is a missing constant, add it to _imgui_compat.py."
            ) from None

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            # Allow monkey-patching wrapper functions (e.g. slider_float).
            _COMPAT_ATTRS[name] = value

    def __dir__(self):
        bundle_names = dir(_imgui)
        compat_names = list(_COMPAT_ATTRS.keys())
        return sorted(set(bundle_names + compat_names))


# The single ``imgui`` object that all BulletLab code should use.
imgui = _ImguiProxy()
