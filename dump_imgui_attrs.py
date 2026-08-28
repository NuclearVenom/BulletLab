import sys, imgui_bundle
print(f"imgui-bundle: {imgui_bundle.__version__}")
from imgui_bundle import imgui
all_attrs = sorted([a for a in dir(imgui) if not a.startswith('_')])
print(f"\nAll imgui attrs ({len(all_attrs)}):")
for a in all_attrs:
    print(f"  {a}")
