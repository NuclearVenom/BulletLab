# Arsenal Guide

[BulletLab Arsenal](https://github.com/NuclearVenom/BulletLab-Arsenal) is the official
robot asset registry for BulletLab — a curated collection of community-contributed,
verified robot packages that load correctly out of the box.

Think of it as PyPI for robotics assets.

---

## Quick Reference

```python
# Permanently install to ~/.bulletlab/packages/
Robot.install("reference_bot")

# Load directly (session cache — no permanent files)
robot = Robot.load("arsenal:reference_bot", sim=sim)
```

---

## Installation

No additional setup is required.  Arsenal integration is built into BulletLab.
An internet connection is needed to fetch packages from the registry.

---

## Robot.install()

Downloads a robot package permanently to the local machine.

```python
from bulletlab import Robot

# Install the default model
Robot.install("reference_bot")

# Install a specific model
Robot.install("reference_bot/BLem1")

# Install to a custom directory (e.g. inside your project)
Robot.install("reference_bot", path="robots/")
Robot.install("reference_bot/BLem1", path="robots/")
```

After installation you can load the robot from its local path:

```python
urdf = Robot.install("reference_bot")
robot = Robot.load(str(urdf), sim=sim)
```

The default install location is `~/.bulletlab/packages/<package_name>/`.

---

## Robot.load() with Arsenal URI

Load a robot directly from the Arsenal registry without permanently installing it.
Assets are downloaded into a **session-scoped temporary cache** and cleaned up
automatically when the Python process exits.

### URI format

```
arsenal:<package_name>
arsenal:<package_name>/<model_id>
```

### Examples

```python
from bulletlab import Simulation, Robot
from bulletlab.core.world import World

sim = Simulation(mode="gui").start()
World(sim).load_plane()

# Default model
robot = Robot.load("arsenal:reference_bot", sim=sim)

# Specific model
robot = Robot.load("arsenal:reference_bot/BLem1", sim=sim)

# With standard Robot.load() parameters
robot = Robot.load(
    "arsenal:reference_bot",
    sim=sim,
    position=(0, 0, 0.5),
    fixed_base=False,
    scale=1.0,
    tilt=((0, 1, 0), 10),
)
```

All `Robot.load()` parameters (`position`, `orientation`, `fixed_base`, `scale`,
`flags`, `tilt`, `name`) work identically with Arsenal sources.

---

## Install vs. Direct Load

| Feature | `Robot.install()` | `Robot.load("arsenal:...")` |
|---|---|---|
| Files on disk after exit | ✅ Permanent | ❌ Deleted automatically |
| Works offline after first use | ✅ Yes | ❌ Requires network each session |
| Clutters local filesystem | Slightly (in `~/.bulletlab/`) | Never |
| Best for | Reproducible research, production | Quick experiments, demos |
| Loading API | `Robot.load(str(installed_path), ...)` | `Robot.load("arsenal:...", ...)` |

---

## Model Resolution

When you use `"arsenal:reference_bot"` (no model specified), BulletLab:

1. Fetches the Arsenal robot manifest from the registry.
2. Locates the `reference_bot` package.
3. Reads the package's `metadata.json`.
4. Selects the model where `"default": true` (or the first model if none is marked).
5. Downloads only the URDF and its referenced mesh files.
6. Rewrites mesh paths to absolute local paths so PyBullet can find them.

When you use `"arsenal:reference_bot/BLem1"`, step 4 selects the model whose `id` or
`display_name` matches `"BLem1"` (case-insensitive).

---

## Session Cache

The session cache is stored in a system temp directory (e.g. `%TEMP%\bulletlab_arsenal_...`
on Windows, `/tmp/bulletlab_arsenal_...` on Linux/macOS).

- **Created** on the first `Robot.load("arsenal:...")` call.
- **Shared** across all Arsenal loads in the same session (no duplicate downloads).
- **Deleted** automatically via `atexit` when the process exits.
- **Never visible** to the user — no cleanup is needed.

---

## Error Handling

All Arsenal errors are subclasses of `ArsenalError`:

```python
from bulletlab import Robot, ArsenalError
from bulletlab.arsenal import (
    PackageNotFoundError,   # Package not in the registry
    ModelNotFoundError,     # Model ID not found in the package
    NetworkError,           # HTTP or connection failure
    ManifestError,          # Manifest unavailable or malformed
    CorruptedPackageError,  # Downloaded file is missing or empty
)

try:
    robot = Robot.load("arsenal:my_package", sim=sim)
except PackageNotFoundError as e:
    print(f"Package not found: {e}")
except ModelNotFoundError as e:
    print(f"Model not found: {e}")
except NetworkError as e:
    print(f"Network failure: {e}")
except ArsenalError as e:
    print(f"Arsenal error: {e}")
```

---

## What Gets Downloaded

Only the files required by the requested model are downloaded:

- The URDF file (entrypoint defined in `metadata.json`).
- All mesh files referenced by `<mesh filename="...">` tags in the URDF.
- No unrelated models, documentation, or verification artifacts.

Mesh paths in the downloaded URDF are automatically rewritten to absolute local paths,
so PyBullet can find every asset regardless of the working directory.

---

## Programmatic Access

You can access the Arsenal subpackage directly for advanced use:

```python
from bulletlab.arsenal import install, DEFAULT_PACKAGES_DIR
from bulletlab.arsenal.resolver import resolve_package, resolve_model
from bulletlab.arsenal.paths import ARSENAL_ROBOTS_MANIFEST_URL

# Inspect the default install location
print(DEFAULT_PACKAGES_DIR)   # ~/.bulletlab/packages

# Resolve without downloading
pkg  = resolve_package("reference_bot")
model = resolve_model("reference_bot", None)
print(model["entrypoint"])    # urdf/BLem1.urdf
```

---

## See Also

- [Robot Guide — Loading from Arsenal](robot_guide.md#loading-from-bulletlab-arsenal)
- [Cookbook — Recipe #12](../cookbook.md#12-loading-from-bulletlab-arsenal)
- [BulletLab Arsenal repository](https://github.com/NuclearVenom/BulletLab-Arsenal)
