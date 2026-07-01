"""
Asset downloader for BulletLab Arsenal.

Downloads a robot package's URDF and all referenced mesh files into a local
directory, then rewrites the URDF's mesh ``filename=`` attributes to absolute
local paths so that PyBullet can find every asset without any search-path
configuration.

This module is used by both the temporary-cache path (``Robot.load``) and
the permanent install path (``Robot.install``).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from bulletlab.arsenal.client import fetch_bytes
from bulletlab.arsenal.exceptions import CorruptedPackageError
from bulletlab.arsenal.paths import ARSENAL_PACKAGE_FILE_URL


def download_package(
    package_name: str,
    entrypoint: str,
    dest_dir: Path,
) -> Path:
    """Download a robot package's URDF and referenced meshes into *dest_dir*.

    Performs the following steps:

    1. Downloads the URDF file from the Arsenal repository.
    2. Parses the URDF to find all ``filename=`` attributes inside
       ``<mesh>`` elements.
    3. Downloads each referenced mesh file, preserving the relative
       directory structure (e.g. ``meshes/base_link.stl``).
    4. Rewrites the URDF's mesh paths to absolute local paths so that
       PyBullet can locate them regardless of the working directory.
    5. Writes the rewritten URDF to *dest_dir* and returns its path.

    Args:
        package_name: Arsenal package directory name (e.g. ``"reference_bot"``).
        entrypoint: Relative path to the URDF within the package
            (e.g. ``"urdf/BLem1.urdf"``).
        dest_dir: Local directory where files will be written.  Created
            automatically if it does not exist.

    Returns:
        Absolute :class:`pathlib.Path` to the downloaded (and rewritten) URDF.

    Raises:
        CorruptedPackageError: If the URDF cannot be fetched, parsed, or if
            a required mesh file cannot be downloaded.

    Example::

        from bulletlab.arsenal.cache import get_session_cache
        cache = get_session_cache() / "reference_bot"
        urdf_path = download_package("reference_bot", "urdf/BLem1.urdf", cache)
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Download the URDF
    # ------------------------------------------------------------------
    urdf_url = ARSENAL_PACKAGE_FILE_URL.format(
        package_name=package_name,
        rel_path=entrypoint,
    )
    try:
        urdf_bytes = fetch_bytes(urdf_url)
    except Exception as exc:
        raise CorruptedPackageError(
            f"Failed to download URDF for package {package_name!r} "
            f"from {urdf_url!r}: {exc}"
        ) from exc

    if not urdf_bytes:
        raise CorruptedPackageError(
            f"Downloaded URDF for {package_name!r} is empty. URL: {urdf_url}"
        )

    urdf_text = urdf_bytes.decode("utf-8")

    # ------------------------------------------------------------------
    # 2. Parse URDF and collect mesh references
    # ------------------------------------------------------------------
    # The URDF entrypoint may be inside a subdirectory (e.g. "urdf/BLem1.urdf").
    # Mesh paths are relative to the URDF file itself, so we need to know
    # the directory portion of the entrypoint to resolve them.
    entrypoint_dir = "/".join(entrypoint.split("/")[:-1])  # e.g. "urdf"

    mesh_refs = _extract_mesh_refs(urdf_text)

    # ------------------------------------------------------------------
    # 3. Download each mesh file
    # ------------------------------------------------------------------
    # Maps original URDF filename string → absolute local path
    local_mesh_paths: dict[str, str] = {}

    for ref in mesh_refs:
        # Normalise: strip any leading "./" or "../" prefix to get a clean
        # package-relative path for the download URL.
        rel_path_for_url = _resolve_ref_to_package_path(ref, entrypoint_dir)

        mesh_url = ARSENAL_PACKAGE_FILE_URL.format(
            package_name=package_name,
            rel_path=rel_path_for_url,
        )

        # Determine local path (mirror the package structure under dest_dir)
        local_mesh_path = dest_dir / rel_path_for_url
        local_mesh_path.parent.mkdir(parents=True, exist_ok=True)

        if not local_mesh_path.exists():
            try:
                mesh_bytes = fetch_bytes(mesh_url)
            except Exception as exc:
                raise CorruptedPackageError(
                    f"Failed to download mesh {ref!r} for package "
                    f"{package_name!r}: {exc}"
                ) from exc
            local_mesh_path.write_bytes(mesh_bytes)

        local_mesh_paths[ref] = str(local_mesh_path.resolve())

    # ------------------------------------------------------------------
    # 4. Rewrite URDF mesh paths to absolute local paths
    # ------------------------------------------------------------------
    rewritten_urdf = _rewrite_mesh_paths(urdf_text, local_mesh_paths)

    # ------------------------------------------------------------------
    # 5. Write the rewritten URDF
    # ------------------------------------------------------------------
    urdf_filename = Path(entrypoint).name
    local_urdf_path = dest_dir / urdf_filename
    local_urdf_path.write_text(rewritten_urdf, encoding="utf-8")

    return local_urdf_path.resolve()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_mesh_refs(urdf_text: str) -> list[str]:
    """Return all unique ``filename`` attribute values inside ``<mesh>`` tags.

    Uses a regex rather than a full XML parse to preserve the original
    document formatting when we rewrite paths later.

    Args:
        urdf_text: Raw URDF file content.

    Returns:
        List of unique filename strings exactly as they appear in the URDF.
    """
    # Match both single-quoted and double-quoted filename= attributes
    # inside <mesh ...> tags.
    pattern = re.compile(
        r"<mesh\b[^>]*\bfilename\s*=\s*(['\"])([^'\"]+)\1",
        re.IGNORECASE,
    )
    seen: set[str] = set()
    refs: list[str] = []
    for m in pattern.finditer(urdf_text):
        ref = m.group(2)
        if ref not in seen:
            seen.add(ref)
            refs.append(ref)
    return refs


def _resolve_ref_to_package_path(ref: str, entrypoint_dir: str) -> str:
    """Resolve a URDF mesh reference to a package-root-relative path.

    URDF mesh filenames are relative to the URDF file itself.  For example,
    if the URDF is at ``urdf/BLem1.urdf`` and it references
    ``"../meshes/base_link.stl"``, the package-relative path is
    ``"meshes/base_link.stl"``.

    Args:
        ref: The raw ``filename`` string from the URDF.
        entrypoint_dir: Directory portion of the entrypoint path
            (e.g. ``"urdf"`` for ``"urdf/BLem1.urdf"``).

    Returns:
        Package-root-relative path string suitable for URL construction.
    """
    # Build a virtual path: entrypoint_dir / ref, then normalise ".."
    if entrypoint_dir:
        combined = f"{entrypoint_dir}/{ref}"
    else:
        combined = ref

    # Use PurePosixPath to resolve ".." components without touching the FS
    from pathlib import PurePosixPath
    resolved = str(PurePosixPath(combined))
    return resolved


def _rewrite_mesh_paths(urdf_text: str, mapping: dict[str, str]) -> str:
    """Replace URDF mesh ``filename`` values with absolute local paths.

    Args:
        urdf_text: Original URDF content.
        mapping: Dict of ``{original_filename_string: absolute_local_path}``.

    Returns:
        Rewritten URDF content as a string.
    """
    for original, local_abs in mapping.items():
        # Replace both single- and double-quoted occurrences
        for quote in ('"', "'"):
            urdf_text = urdf_text.replace(
                f'filename={quote}{original}{quote}',
                f'filename={quote}{local_abs}{quote}',
            )
    return urdf_text
