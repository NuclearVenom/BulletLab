# Deep API structure dump for any installed imgui-bundle version
import sys
import imgui_bundle

print(f"imgui-bundle: {imgui_bundle.__version__}")
from imgui_bundle import imgui, implot

print(f"\n--- imgui module type: {type(imgui)} ---")
# Top 40 attrs
all_attrs = [a for a in dir(imgui) if not a.startswith('_')]
print(f"Total attrs: {len(all_attrs)}")
# Specifically look for Col-related and context-related
col_attrs = [a for a in all_attrs if 'col' in a.lower() or 'color' in a.lower()]
ctx_attrs = [a for a in all_attrs if 'context' in a.lower() or 'frame' in a.lower()]
flag_attrs = [a for a in all_attrs if 'flags' in a.lower() or 'Flag' in a]
print(f"\nCol-related attrs: {col_attrs}")
print(f"\nContext/frame attrs: {ctx_attrs}")
print(f"\nFlag attrs: {flag_attrs[:20]}")

# Check if it's an older-style API
print(f"\nHas ImGuiCol_: {hasattr(imgui, 'ImGuiCol_')}")
print(f"Has Col_: {hasattr(imgui, 'Col_')}")
print(f"Has create_context: {hasattr(imgui, 'create_context')}")
print(f"Has CreateContext: {hasattr(imgui, 'CreateContext')}")
print(f"Has new_frame: {hasattr(imgui, 'new_frame')}")
print(f"Has NewFrame: {hasattr(imgui, 'NewFrame')}")
print(f"Has render: {hasattr(imgui, 'render')}")
print(f"Has Render: {hasattr(imgui, 'Render')}")
print(f"Has get_style: {hasattr(imgui, 'get_style')}")
print(f"Has GetStyle: {hasattr(imgui, 'GetStyle')}")
print(f"Has slider_float: {hasattr(imgui, 'slider_float')}")
print(f"Has SliderFloat: {hasattr(imgui, 'SliderFloat')}")
print(f"Has ChildFlags_: {hasattr(imgui, 'ChildFlags_')}")
print(f"Has WindowFlags_: {hasattr(imgui, 'WindowFlags_')}")

# Check for imgui_bundle.glfw 
try:
    import imgui_bundle.glfw as _glfw
    print(f"\nimgui_bundle.glfw: EXISTS ({dir(_glfw)[:5]}...)")
except ImportError as e:
    print(f"\nimgui_bundle.glfw: ABSENT ({e})")

# Check for imgui_bundle attributes (top-level)
top = [a for a in dir(imgui_bundle) if not a.startswith('_')]
print(f"\nimgui_bundle top-level ({len(top)}): {top[:20]}")

# Check if pydantic is available
try:
    import pydantic
    print(f"\npydantic: {pydantic.__version__}")
except ImportError:
    print("\npydantic: NOT installed")

try:
    import munch
    print(f"munch: {munch.__version__}")
except ImportError:
    print("munch: NOT installed")
