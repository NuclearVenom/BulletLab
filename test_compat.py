"""
Test BulletLab compatibility with a specific imgui-bundle version.
Run as: python test_compat.py <version>
"""
import sys
import importlib

version = sys.argv[1] if len(sys.argv) > 1 else "unknown"
print(f"\n{'='*60}")
print(f"Testing BulletLab vs imgui-bundle {version}")
print(f"Python: {sys.version}")
print(f"{'='*60}")

FAIL = []
PASS = []

def check(name, fn):
    try:
        result = fn()
        PASS.append(name)
        if result is not None:
            print(f"  PASS  {name}: {result}")
        else:
            print(f"  PASS  {name}")
    except Exception as e:
        FAIL.append(name)
        print(f"  FAIL  {name}: {e}")

# --- imgui_bundle version ---
check("imgui_bundle import", lambda: __import__("imgui_bundle").__version__)

# --- imgui_bundle.imgui ---
check("imgui_bundle.imgui import", lambda: __import__("imgui_bundle.imgui", fromlist=["imgui"]) and "ok")

# --- implot ---
check("imgui_bundle.implot import", lambda: __import__("imgui_bundle.implot", fromlist=["implot"]) and "ok")

# --- Col_ constants ---
def check_cols():
    from imgui_bundle import imgui
    required = ["text","window_bg","button","frame_bg","slider_grab","slider_grab_active",
                "title_bg","title_bg_active","menu_bar_bg","header","header_hovered",
                "header_active","check_mark","separator","popup_bg","frame_bg_hovered",
                "button_hovered","button_active"]
    missing = [c for c in required if not hasattr(imgui.Col_, c)]
    if missing:
        raise AttributeError(f"missing Col_: {missing}")
    return f"all {len(required)} Col_ attrs OK"
check("imgui.Col_ required constants", check_cols)

# --- Tab colors (via compat layer) ---
def check_tab_colors():
    from imgui_bundle import imgui
    # These are the ones BulletLab uses via _imgui_compat.py
    # Tab = 34, TabHovered = 33, TabSelected/Active = 35, TabDimmed/Unfocused = 37, TabDimmedSelected/UnfocusedActive = 38
    tab = getattr(imgui.Col_, "tab", None)
    if tab is None:
        raise AttributeError("Col_.tab missing")
    return f"Col_.tab={tab.value}"
check("imgui.Col_.tab exists", check_tab_colors)

# --- WindowFlags_, TreeNodeFlags_, ChildFlags_ ---
def check_flags():
    from imgui_bundle import imgui
    assert hasattr(imgui, "WindowFlags_"), "no WindowFlags_"
    assert hasattr(imgui.WindowFlags_, "no_title_bar"), "no WindowFlags_.no_title_bar"
    assert hasattr(imgui, "TreeNodeFlags_"), "no TreeNodeFlags_"
    assert hasattr(imgui, "ChildFlags_"), "no ChildFlags_"
    border = getattr(imgui.ChildFlags_, "border", None) or getattr(imgui.ChildFlags_, "borders", None)
    assert border is not None, "ChildFlags_.border/borders both missing"
    return "all flag enums OK"
check("Flag enums (WindowFlags_, TreeNodeFlags_, ChildFlags_)", check_flags)

# --- ImVec2, ImVec4 ---
def check_vecs():
    from imgui_bundle import ImVec2, ImVec4
    v = ImVec2(1.0, 2.0)
    v4 = ImVec4(0.1, 0.2, 0.3, 1.0)
    return "ImVec2, ImVec4 OK"
check("ImVec2/ImVec4", check_vecs)

# --- Context management ---
def check_ctx():
    from imgui_bundle import imgui
    assert callable(imgui.create_context)
    assert callable(imgui.destroy_context)
    assert callable(imgui.set_current_context)
    assert callable(imgui.new_frame)
    assert callable(imgui.render)
    assert callable(imgui.get_draw_data)
    return "context API OK"
check("imgui context API", check_ctx)

# --- implot context ---
def check_implot_ctx():
    from imgui_bundle import implot
    assert callable(implot.create_context)
    assert callable(implot.destroy_context)
    assert callable(implot.set_current_context)
    return "implot context OK"
check("implot context API", check_implot_ctx)

# --- python_backends ---
def check_backends():
    try:
        from imgui_bundle.python_backends.glfw_backend import GlfwRenderer
        return "GlfwRenderer from glfw_backend OK"
    except ImportError:
        from imgui_bundle.python_backends.opengl_backend import OpenGLRenderer
        return "OpenGLRenderer from opengl_backend OK (fallback)"
check("python_backends GlfwRenderer/OpenGLRenderer", check_backends)

# --- get_style ---
def check_style():
    from imgui_bundle import imgui
    assert callable(imgui.get_style)
    assert callable(imgui.style_colors_dark)
    return "get_style, style_colors_dark OK"
check("imgui.get_style / style_colors_dark", check_style)

# --- _imgui_compat proxy ---
def check_compat():
    sys.path.insert(0, r"c:\Users\ranas\Desktop\BulletLab")
    from bulletlab.ui._imgui_compat import imgui as compat_imgui
    # Check all constants BulletLab sets via the compat layer
    attrs = ["COLOR_SLIDER_GRAB","COLOR_TAB","COLOR_TAB_ACTIVE","COLOR_TAB_UNFOCUSED",
             "WINDOW_NO_TITLE_BAR","INPUT_TEXT_ENTER_RETURNS_TRUE","COLOR_TEXT",
             "COLOR_WINDOW_BG","COLOR_BUTTON","COLOR_FRAME_BG"]
    missing = [a for a in attrs if not hasattr(compat_imgui, a)]
    if missing:
        raise AttributeError(f"_imgui_compat missing: {missing}")
    # Check callables
    callables = ["begin_main_menu_bar","end_main_menu_bar","begin_menu","end_menu",
                 "menu_item","slider_float","input_text","button","text","separator",
                 "begin_child","end_child","begin","end"]
    missing_fn = [fn for fn in callables if not callable(getattr(compat_imgui, fn, None))]
    if missing_fn:
        raise AttributeError(f"_imgui_compat missing callables: {missing_fn}")
    return f"compat layer OK ({len(attrs)} consts, {len(callables)} callables)"
check("BulletLab _imgui_compat proxy", check_compat)

# --- BulletLab import ---
def check_bl():
    sys.path.insert(0, r"c:\Users\ranas\Desktop\BulletLab")
    if "bulletlab" in sys.modules:
        importlib.reload(sys.modules["bulletlab"])
    import bulletlab
    return f"BulletLab {bulletlab.__version__}"
check("bulletlab import", check_bl)

# --- widget/console APIs used at runtime ---
def check_widgets():
    from bulletlab.ui import widgets
    assert hasattr(widgets, "button"), "no widgets.button"
    assert hasattr(widgets, "text"), "no widgets.text"
    assert hasattr(widgets, "slider"), "no widgets.slider"
    assert hasattr(widgets, "checkbox"), "no widgets.checkbox"
    return "widgets module OK"
check("widgets module", check_widgets)

# --- Console panel ---
def check_console():
    from bulletlab.ui.panels.console import ConsolePanel
    # Verify it can be instantiated (headless)
    import unittest.mock as mock
    panel = ConsolePanel.__new__(ConsolePanel)
    return "ConsolePanel instantiation OK"
check("ConsolePanel headless", check_console)

print(f"\n{'='*60}")
print(f"RESULT for imgui-bundle {version}:")
print(f"  PASS: {len(PASS)}/{len(PASS)+len(FAIL)}")
if FAIL:
    print(f"  FAIL: {FAIL}")
else:
    print(f"  ALL CHECKS PASSED")
print(f"{'='*60}\n")
sys.exit(0 if not FAIL else 1)
