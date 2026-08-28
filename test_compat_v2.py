"""
Corrected BulletLab + imgui-bundle compatibility test.
Run as: python test_compat_v2.py <version>

Fixes from v1:
- Tests the CORRECT compat attr names (COLOR_WINDOW_BACKGROUND not COLOR_WINDOW_BG)
- Does not test opengl_backend as a hard requirement (it's an optional fallback)
- Requires numpy to be present (pre-installed externally)
"""
import sys
import importlib

version = sys.argv[1] if len(sys.argv) > 1 else "unknown"
print(f"\n{'='*60}")
print(f"Testing BulletLab vs imgui-bundle {version}")
print(f"Python: {sys.version.split()[0]}")
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
check("imgui_bundle import + version", lambda: __import__("imgui_bundle").__version__)

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
                "button_hovered","button_active","tab"]
    missing = [c for c in required if not hasattr(imgui.Col_, c)]
    if missing:
        raise AttributeError(f"missing Col_: {missing}")
    return f"all {len(required)} required Col_ attrs OK"
check("imgui.Col_ required constants + tab", check_cols)

# --- WindowFlags_, TreeNodeFlags_, ChildFlags_ ---
def check_flags():
    from imgui_bundle import imgui
    assert hasattr(imgui, "WindowFlags_"), "no WindowFlags_"
    assert hasattr(imgui.WindowFlags_, "no_title_bar"), "no WindowFlags_.no_title_bar"
    assert hasattr(imgui, "TreeNodeFlags_"), "no TreeNodeFlags_"
    assert hasattr(imgui, "ChildFlags_"), "no ChildFlags_"
    border = getattr(imgui.ChildFlags_, "border", None) or getattr(imgui.ChildFlags_, "borders", None)
    assert border is not None, "ChildFlags_.border/borders both missing"
    return "WindowFlags_, TreeNodeFlags_, ChildFlags_ OK"
check("Flag enums", check_flags)

# --- ImVec2, ImVec4 ---
check("ImVec2/ImVec4", lambda: __import__("imgui_bundle", fromlist=["ImVec2"]).ImVec2(1.0, 2.0) and "OK")

# --- Context management ---
def check_ctx():
    from imgui_bundle import imgui
    for fn in ["create_context","destroy_context","set_current_context","new_frame","render","get_draw_data"]:
        assert callable(getattr(imgui, fn, None)), f"imgui.{fn} not callable"
    return "context API OK"
check("imgui context API", check_ctx)

# --- implot context ---
def check_implot_ctx():
    from imgui_bundle import implot
    for fn in ["create_context","destroy_context","set_current_context"]:
        assert callable(getattr(implot, fn, None)), f"implot.{fn} not callable"
    return "implot context OK"
check("implot context API", check_implot_ctx)

# --- python_backends (glfw_backend is primary; opengl is optional fallback) ---
def check_backends():
    # glfw_backend is required (primary path in app.py)
    from imgui_bundle.python_backends.glfw_backend import GlfwRenderer
    return "GlfwRenderer from glfw_backend OK"
check("python_backends glfw_backend.GlfwRenderer", check_backends)

# --- get_style ---
def check_style():
    from imgui_bundle import imgui
    assert callable(imgui.get_style)
    assert callable(imgui.style_colors_dark)
    return "get_style, style_colors_dark OK"
check("imgui.get_style / style_colors_dark", check_style)

# --- _imgui_compat proxy: CORRECT attribute names ---
def check_compat():
    # Add bulletlab to path
    if r"c:\Users\ranas\Desktop\BulletLab" not in sys.path:
        sys.path.insert(0, r"c:\Users\ranas\Desktop\BulletLab")
    # Force reimport after imgui-bundle switch
    for mod in list(sys.modules.keys()):
        if mod.startswith("bulletlab.ui._imgui_compat"):
            del sys.modules[mod]
    from bulletlab.ui._imgui_compat import imgui as compat_imgui
    # CORRECT attr names from _imgui_compat.py lines 44-98
    attrs = [
        "COLOR_TEXT", "COLOR_TEXT_DISABLED",
        "COLOR_WINDOW_BACKGROUND", "COLOR_CHILD_BACKGROUND", "COLOR_POPUP_BACKGROUND",
        "COLOR_FRAME_BACKGROUND", "COLOR_FRAME_BACKGROUND_HOVERED",
        "COLOR_TITLE_BACKGROUND", "COLOR_TITLE_BACKGROUND_ACTIVE",
        "COLOR_MENUBAR_BACKGROUND", "COLOR_SCROLLBAR_BACKGROUND",
        "COLOR_CHECK_MARK", "COLOR_SLIDER_GRAB", "COLOR_SLIDER_GRAB_ACTIVE",
        "COLOR_BUTTON", "COLOR_BUTTON_HOVERED", "COLOR_BUTTON_ACTIVE",
        "COLOR_HEADER", "COLOR_HEADER_HOVERED", "COLOR_HEADER_ACTIVE",
        "COLOR_SEPARATOR",
        "COLOR_TAB", "COLOR_TAB_HOVERED", "COLOR_TAB_ACTIVE",
        "COLOR_TAB_UNFOCUSED", "COLOR_TAB_UNFOCUSED_ACTIVE",
        "WINDOW_NO_TITLE_BAR", "INPUT_TEXT_ENTER_RETURNS_TRUE",
    ]
    missing = [a for a in attrs if not hasattr(compat_imgui, a)]
    if missing:
        raise AttributeError(f"_imgui_compat missing attrs: {missing}")
    callables = ["begin_main_menu_bar","end_main_menu_bar","begin_menu","end_menu",
                 "menu_item","slider_float","input_text","button","text","separator",
                 "begin_child","end_child","begin","end","begin_tab_bar","begin_tab_item"]
    missing_fn = [fn for fn in callables if not callable(getattr(compat_imgui, fn, None))]
    if missing_fn:
        raise AttributeError(f"_imgui_compat missing callables: {missing_fn}")
    return f"compat layer OK ({len(attrs)} consts, {len(callables)} callables)"
check("BulletLab _imgui_compat proxy (correct attr names)", check_compat)

# --- BulletLab import ---
def check_bl():
    if r"c:\Users\ranas\Desktop\BulletLab" not in sys.path:
        sys.path.insert(0, r"c:\Users\ranas\Desktop\BulletLab")
    import bulletlab
    return f"BulletLab {bulletlab.__version__}"
check("bulletlab import", check_bl)

# --- widgets module ---
def check_widgets():
    if r"c:\Users\ranas\Desktop\BulletLab" not in sys.path:
        sys.path.insert(0, r"c:\Users\ranas\Desktop\BulletLab")
    from bulletlab.ui import widgets
    for name in ["button","text","slider","checkbox","drag_float"]:
        assert hasattr(widgets, name), f"no widgets.{name}"
    return "widgets module OK"
check("widgets module", check_widgets)

# --- ChildFlags_.border or .borders ---
def check_childflag():
    from imgui_bundle import imgui
    b = getattr(imgui.ChildFlags_, "border", None) or getattr(imgui.ChildFlags_, "borders", None)
    assert b is not None
    name = "border" if hasattr(imgui.ChildFlags_, "border") else "borders"
    return f"ChildFlags_.{name}={b.value}"
check("ChildFlags_.border or .borders", check_childflag)

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
