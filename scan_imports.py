import ast, sys
from pathlib import Path

root = Path(r'c:\Users\ranas\Desktop\BulletLab\bulletlab')
stdlib = set(sys.stdlib_module_names)
stdlib.update(['typing_extensions', 'types', '__future__'])

def extract_imports(path):
    try:
        src = path.read_text(encoding='utf-8', errors='replace')
        tree = ast.parse(src)
    except:
        return []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                imports.append(node.module.split('.')[0])
    return imports

all_imports = {}
for py in root.rglob('*.py'):
    rel = str(py.relative_to(root))
    imports = extract_imports(py)
    for imp in imports:
        if imp in stdlib or imp.startswith('bulletlab') or imp.startswith('_'):
            continue
        if imp not in all_imports:
            all_imports[imp] = set()
        all_imports[imp].add(rel)

for pkg, files in sorted(all_imports.items()):
    unique_files = sorted(files)
    print(f'{pkg:20s}  <- {", ".join(unique_files[:4])}{"..." if len(unique_files)>4 else ""}')
