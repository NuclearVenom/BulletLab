"""
URDF discovery utilities for BulletLab.

Provides helpers for finding URDF files in the pybullet_data asset library
and scanning user-provided search paths.

Example::

    from bulletlab.utils.urdf_utils import find_urdf, list_available_urdfs

    path = find_urdf("kuka_iiwa/model.urdf")
    print(list_available_urdfs())
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pybullet_data


def get_pybullet_data_path() -> Path:
    """Return the path to the pybullet_data asset directory.

    Returns:
        :class:`pathlib.Path` pointing to pybullet_data.

    Example::

        data_path = get_pybullet_data_path()
    """
    return Path(pybullet_data.getDataPath())


def find_urdf(
    filename: str,
    extra_search_paths: list[str | Path] | None = None,
) -> Path:
    """Search for a URDF file by name.

    Searches in the following order:
    1. Absolute path (if ``filename`` is absolute and exists)
    2. Extra user-provided search paths
    3. pybullet_data directory (recursively)

    Args:
        filename: Filename or relative path (e.g. ``"kuka_iiwa/model.urdf"``).
        extra_search_paths: Additional directories to search.

    Returns:
        Resolved :class:`pathlib.Path` to the URDF.

    Raises:
        FileNotFoundError: If the file cannot be found in any search location.

    Example::

        path = find_urdf("plane.urdf")
        path = find_urdf("kuka_iiwa/model.urdf")
    """
    # 1. Absolute path
    p = Path(filename)
    if p.is_absolute() and p.exists():
        return p

    # 2. Extra search paths
    search_roots: list[Path] = []
    if extra_search_paths:
        search_roots.extend(Path(sp) for sp in extra_search_paths)

    # 3. pybullet_data
    search_roots.append(get_pybullet_data_path())

    for root in search_roots:
        # Direct join
        candidate = root / filename
        if candidate.exists():
            return candidate
        # Recursive search by basename
        basename = Path(filename).name
        for found in root.rglob(basename):
            if found.is_file():
                return found

    raise FileNotFoundError(
        f"URDF/MJCF file not found: {filename!r}. "
        f"Searched: {[str(r) for r in search_roots]}"
    )


def list_available_urdfs(max_results: int = 200) -> list[str]:
    """List URDF and MJCF files available in pybullet_data.

    Args:
        max_results: Maximum number of results to return.

    Returns:
        List of relative paths (relative to pybullet_data root).

    Example::

        for name in list_available_urdfs():
            print(name)
    """
    root = get_pybullet_data_path()
    results: list[str] = []
    for ext in ("*.urdf", "*.xml", "*.sdf"):
        for path in root.rglob(ext):
            rel = str(path.relative_to(root))
            results.append(rel)
            if len(results) >= max_results:
                return sorted(results)
    return sorted(results)
