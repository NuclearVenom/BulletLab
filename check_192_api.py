from imgui_bundle import imgui
import imgui_bundle

print(f"imgui-bundle: {imgui_bundle.__version__}")

names = ['window_bg', 'frame_bg', 'child_bg', 'popup_bg', 'border', 'border_shadow',
         'frame_bg_hovered', 'frame_bg_active', 'title_bg', 'title_bg_active',
         'title_bg_collapsed', 'menu_bar_bg', 'scrollbar_bg', 'scrollbar_grab',
         'scrollbar_grab_hovered', 'scrollbar_grab_active', 'check_mark',
         'slider_grab', 'slider_grab_active', 'button', 'button_hovered', 'button_active',
         'header', 'header_hovered', 'header_active', 'separator',
         'separator_hovered', 'separator_active', 'resize_grip', 'resize_grip_hovered',
         'resize_grip_active', 'tab', 'tab_hovered', 'tab_selected', 'tab_dimmed',
         'tab_dimmed_selected', 'plot_lines', 'plot_lines_hovered',
         'plot_histogram', 'plot_histogram_hovered', 'table_header_bg',
         'table_border_strong', 'table_border_light', 'table_row_bg', 'table_row_bg_alt',
         'text_selected_bg', 'drag_drop_target', 'nav_highlight',
         'nav_windowing_highlight', 'nav_windowing_dim_bg', 'modal_window_dim_bg',
         'text', 'text_disabled']

missing = [n for n in names if not hasattr(imgui.Col_, n)]
print(f"Col_ present: {len(names)-len(missing)}/{len(names)}")
print(f"Col_ missing: {missing}")

try:
    from imgui_bundle.python_backends.opengl_backend import OpenGLRenderer
    print("opengl_backend: EXISTS")
except ImportError as e:
    print(f"opengl_backend: REMOVED - {e}")

try:
    from imgui_bundle.python_backends.glfw_backend import GlfwRenderer
    print("glfw_backend: EXISTS")
except ImportError as e:
    print(f"glfw_backend: MISSING - {e}")

# Check ALL available Col_ names
all_col = [n for n in dir(imgui.Col_) if not n.startswith('_')]
print(f"\nAll Col_ members in 1.92.900: {all_col}")
