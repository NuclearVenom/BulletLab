"""
BulletLab Arsenal — robot asset registry integration.

Provides ``Robot.install()`` and ``Robot.load("arsenal:...")`` support.

Quick reference::

    from bulletlab import Robot, Simulation

    # Permanently install to ~/.bulletlab/packages/
    Robot.install("reference_bot")
    Robot.install("reference_bot/BLem1", path="robots/")

    # Load directly (uses a session-scoped temp cache)
    sim = Simulation().start()
    robot = Robot.load("arsenal:reference_bot", sim=sim)
    robot = Robot.load("arsenal:reference_bot/BLem1", sim=sim, position=(0, 0, 0.5))

Public API
----------
- :func:`install` — install a package permanently
- :exc:`ArsenalError` — base exception for all Arsenal errors
- :exc:`PackageNotFoundError`
- :exc:`ModelNotFoundError`
- :exc:`NetworkError`
- :exc:`ManifestError`
- :exc:`CorruptedPackageError`
"""

from __future__ import annotations

from bulletlab.arsenal.exceptions import (
    ArsenalError,
    CorruptedPackageError,
    ManifestError,
    ModelNotFoundError,
    NetworkError,
    PackageNotFoundError,
)
from bulletlab.arsenal.installer import install
from bulletlab.arsenal.paths import DEFAULT_PACKAGES_DIR

__all__ = [
    "install",
    "DEFAULT_PACKAGES_DIR",
    "ArsenalError",
    "PackageNotFoundError",
    "ModelNotFoundError",
    "NetworkError",
    "ManifestError",
    "CorruptedPackageError",
]
