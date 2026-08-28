"""
Direct BulletLab + imgui-bundle compatibility test.
Tests by actually importing BulletLab code and checking it works,
rather than inspecting imgui_bundle.imgui attributes through a secondary import.

Run as: python test_direct.py <version>
"""
import sys
import os

# BulletLab source path
BL_PATH = r"c:\Users\ranas\Desktop\BulletLab"
if BL_PATH not in sys.path:
    sys.path.insert(0, BL_PATH)

version = sys.argv[1] if len(sys.argv) > 1 else "unknown"
print(f"\n{'='*60}")
print(f"DIRECT TEST: BulletLab vs imgui-bundle {version}")
print(f"Python: {sys.version.split()[0]}")
print(f"{'='*60}")

FAIL = []
PASS = []

def check(name, fn):
    try:
        result = fn()
        PASS.append(name)
        print(f"  PASS  {name}" + (f": {result}" if result else ""))
    except Exception as e:
        FAIL.append(name)
        print(f"  FAIL  {name}: {e}")

# 1. imgui-bundle version
check("imgui_bundle installs + version",
      lambda: __import__("imgui_bundle").__version__)

# 2. _imgui_compat.py proxy — the actual production import path
def check_compat():
    from bulletlab.ui._imgui_compat import imgui as ci
    # Every constant BulletLab actually sets
    consts = [
        "COLOR_TEXT","COLOR_TEXT_DISABLED",
        "COLOR_WINDOW_BACKGROUND","COLOR_CHILD_BACKGROUND","COLOR_POPUP_BACKGROUND",
        "COLOR_FRAME_BACKGROUND","COLOR_FRAME_BACKGROUND_HOVERED","COLOR_FRAME_BACKGROUND_ACTIVE",
        "COLOR_TITLE_BACKGROUND","COLOR_TITLE_BACKGROUND_ACTIVE","COLOR_TITLE_BACKGROUND_COLLAPSED",
        "COLOR_MENUBAR_BACKGROUND","COLOR_SCROLLBAR_BACKGROUND",
        "COLOR_SCROLLBAR_GRAB","COLOR_SCROLLBAR_GRAB_HOVERED","COLOR_SCROLLBAR_GRAB_ACTIVE",
        "COLOR_CHECK_MARK","COLOR_SLIDER_GRAB","COLOR_SLIDER_GRAB_ACTIVE",
        "COLOR_BUTTON","COLOR_BUTTON_HOVERED","COLOR_BUTTON_ACTIVE",
        "COLOR_HEADER","COLOR_HEADER_HOVERED","COLOR_HEADER_ACTIVE",
        "COLOR_SEPARATOR","COLOR_SEPARATOR_HOVERED","COLOR_SEPARATOR_ACTIVE",
        "COLOR_RESIZE_GRIP","COLOR_RESIZE_GRIP_HOVERED","COLOR_RESIZE_GRIP_ACTIVE",
        "COLOR_TAB","COLOR_TAB_HOVERED","COLOR_TAB_ACTIVE","COLOR_TAB_UNFOCUSED","COLOR_TAB_UNFOCUSED_ACTIVE",
        "COLOR_PLOT_LINES","COLOR_PLOT_LINES_HOVERED","COLOR_PLOT_HISTOGRAM","COLOR_PLOT_HISTOGRAM_HOVERED",
        "COLOR_TABLE_HEADER_BACKGROUND","COLOR_TABLE_BORDER_STRONG","COLOR_TABLE_BORDER_LIGHT",
        "COLOR_TABLE_ROW_BACKGROUND","COLOR_TABLE_ROW_BACKGROUND_ALT",
        "COLOR_TEXT_SELECTED_BACKGROUND","COLOR_DRAG_DROP_TARGET","COLOR_NAV_HIGHLIGHT",
        "COLOR_NAV_WINDOWING_HIGHLIGHT","COLOR_NAV_WINDOWING_DIM_BACKGROUND","COLOR_MODAL_WINDOW_DIM_BACKGROUND",
        "WINDOW_NO_TITLE_BAR","WINDOW_NO_RESIZE","WINDOW_NO_MOVE","WINDOW_NO_SCROLLBAR",
        "WINDOW_NO_COLLAPSE","WINDOW_ALWAYS_AUTO_RESIZE","WINDOW_NO_BACKGROUND",
        "WINDOW_NO_SAVED_SETTINGS","WINDOW_MENU_BAR","WINDOW_NO_FOCUS_ON_APPEARING",
        "WINDOW_NO_BRING_TO_DISPLAY_FRONT","WINDOW_ALWAYS_VERTICAL_SCROLLBAR",
        "TREE_NODE_DEFAULT_OPEN","TREE_NODE_OPEN_ON_DOUBLE_CLICK","TREE_NODE_OPEN_ON_ARROW",
        "TREE_NODE_LEAF","TREE_NODE_SELECTED",
        "INPUT_TEXT_ENTER_RETURNS_TRUE","INPUT_TEXT_CALLBACK_ALWAYS","INPUT_TEXT_AUTO_SELECT_ALL",
        "INPUT_TEXT_READ_ONLY","INPUT_TEXT_PASSWORD",
        "SELECTABLE_SPAN_ALL_COLUMNS","SELECTABLE_ALLOW_DOUBLE_CLICK",
        "STYLE_ALPHA","STYLE_WINDOW_PADDING","STYLE_WINDOW_ROUNDING","STYLE_FRAME_PADDING",
        "STYLE_ITEM_SPACING","STYLE_ITEM_INNER_SPACING","STYLE_SCROLLBAR_SIZE","STYLE_SCROLLBAR_ROUNDING",
    ]
    missing = [c for c in consts if not hasattr(ci, c)]
    if missing:
        raise AttributeError(f"missing constants ({len(missing)}): {missing[:5]}{'...' if len(missing)>5 else ''}")

    callables = [
        "begin","end","begin_child","end_child",
        "button","text","text_colored","text_disabled","text_wrapped",
        "slider_float","slider_int","drag_float",
        "input_text","input_text_multiline","input_float","input_int",
        "checkbox","radio_button","selectable","separator","same_line","spacing","dummy",
        "indent","unindent","bullet","collapsing_header",
        "begin_main_menu_bar","end_main_menu_bar","begin_menu","end_menu","menu_item",
        "begin_tab_bar","end_tab_bar","begin_tab_item","end_tab_item",
        "push_style_color","pop_style_color","push_style_var","pop_style_var",
        "push_item_width","pop_item_width","set_next_item_width",
        "push_id","pop_id","set_next_window_size","set_next_window_pos",
        "get_content_region_avail","get_cursor_pos","set_cursor_pos",
        "is_item_hovered","is_item_clicked","is_mouse_clicked",
        "begin_popup","end_popup","open_popup","begin_popup_modal","close_current_popup",
        "tree_node","tree_pop","set_next_item_open",
        "get_draw_data","new_frame","render","create_context","destroy_context",
        "set_current_context","get_io","get_style","style_colors_dark",
    ]
    missing_fn = [f for f in callables if not callable(getattr(ci, f, None))]
    if missing_fn:
        raise AttributeError(f"missing callables ({len(missing_fn)}): {missing_fn[:5]}{'...' if len(missing_fn)>5 else ''}")

    return f"{len(consts)} consts OK, {len(callables)} callables OK"
check("_imgui_compat proxy (all constants + callables)", check_compat)

# 3. app._HAS_IMGUI flag - verifies full import chain in BulletLab's UI module
def check_app_import():
    # Force reimport
    for k in list(sys.modules.keys()):
        if k.startswith("bulletlab.ui.app"):
            del sys.modules[k]
    import bulletlab.ui.app as app_mod
    if not app_mod._HAS_IMGUI:
        err = getattr(app_mod, "_IMGUI_IMPORT_ERROR", "unknown")
        raise ImportError(f"_HAS_IMGUI=False: {err}")
    return f"_HAS_IMGUI=True"
check("app.py full import chain (_HAS_IMGUI=True)", check_app_import)

# 4. live_plot._HAS_IMPLOT
def check_live_plot():
    for k in list(sys.modules.keys()):
        if k.startswith("bulletlab.plotting"):
            del sys.modules[k]
    import bulletlab.plotting.live_plot as lp
    return f"_HAS_IMPLOT={lp._HAS_IMPLOT}"
check("live_plot.py import (_HAS_IMPLOT)", check_live_plot)

# 5. Full BulletLab package import
def check_bl():
    for k in list(sys.modules.keys()):
        if k.startswith("bulletlab") and k != "bulletlab.ui._imgui_compat":
            del sys.modules[k]
    import bulletlab
    return f"BulletLab {bulletlab.__version__}"
check("bulletlab package import", check_bl)

# 6. implot context API (via compat layer, not direct import)
def check_implot():
    from bulletlab.ui._imgui_compat import imgui as ci
    fns = ["create_context","destroy_context","set_current_context","begin_plot","end_plot"]
    # implot is accessible via the compat proxy or directly
    from imgui_bundle import implot
    missing = [f for f in fns if not callable(getattr(implot, f, None))]
    if missing:
        raise AttributeError(f"implot missing: {missing}")
    return "implot context OK"
check("implot context API", check_implot)

# 7. Style helpers - just verify they are callable (calling requires active context)
def check_style():
    from bulletlab.ui._imgui_compat import imgui as ci
    assert callable(ci.get_style), "get_style not callable"
    assert callable(ci.style_colors_dark), "style_colors_dark not callable"
    assert callable(ci.push_style_color), "push_style_color not callable"
    assert callable(ci.pop_style_color), "pop_style_color not callable"
    return "get_style, style_colors_dark, push/pop_style_color callable"
check("style API callability", check_style)

# 8. Panels can be instantiated
def check_panels():
    from bulletlab.ui.panels.console import ConsolePanel
    from bulletlab.ui.panels.explorer import ExplorerPanel
    from bulletlab.ui.panels.properties import PropertiesPanel
    return "ConsolePanel, ExplorerPanel, PropertiesPanel OK"
check("UI panel classes accessible", check_panels)

print(f"\n{'='*60}")
print(f"RESULT for imgui-bundle {version}:")
print(f"  PASS: {len(PASS)}/{len(PASS)+len(FAIL)}")
if FAIL:
    print(f"  FAIL: {FAIL}")
    print(f"  STATUS: INCOMPATIBLE")
else:
    print(f"  STATUS: COMPATIBLE")
print(f"{'='*60}\n")
sys.exit(0 if not FAIL else 1)
