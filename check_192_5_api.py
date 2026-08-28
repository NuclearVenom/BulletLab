import sys
import imgui_bundle

print(f"imgui-bundle: {imgui_bundle.__version__}")
print(f"Python: {sys.version}")

# 1. Top-level structure
from imgui_bundle import imgui, implot
print(f"\nTop-level imgui module type: {type(imgui)}")
print(f"Has Col_: {hasattr(imgui, 'Col_')}")
print(f"Has create_context: {hasattr(imgui, 'create_context')}")
print(f"Has get_style: {hasattr(imgui, 'get_style')}")
print(f"Has slider_float: {hasattr(imgui, 'slider_float')}")
print(f"Has WindowFlags_: {hasattr(imgui, 'WindowFlags_')}")

# 2. Dump some top-level attributes to understand structure
attrs = [a for a in dir(imgui) if not a.startswith('_')]
print(f"\nTop-level attrs ({len(attrs)} total):")
# Print the first 30 and last 10 to understand structure
for a in attrs[:20]:
    print(f"  {a}")
print("  ...")
for a in attrs[-5:]:
    print(f"  {a}")

# 3. Check submodule structure
print(f"\nimgui_bundle dir (top 30):")
bundle_attrs = [a for a in dir(imgui_bundle) if not a.startswith('_')]
for a in bundle_attrs[:30]:
    print(f"  {a}")

# 4. Check python_backends
try:
    from imgui_bundle.python_backends.glfw_backend import GlfwRenderer
    print(f"\nglfw_backend.GlfwRenderer: EXISTS")
except ImportError as e:
    print(f"\nglfw_backend: MISSING - {e}")

try:
    from imgui_bundle.python_backends.opengl_backend import OpenGLRenderer
    print(f"opengl_backend.OpenGLRenderer: EXISTS")
except ImportError as e:
    print(f"opengl_backend: REMOVED - {e}")
