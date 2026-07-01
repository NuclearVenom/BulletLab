"""
Permanent robot package installer for BulletLab Arsenal.

Provides :func:`install` which downloads an Arsenal robot package to a
persistent location on the local machine (``~/.bulletlab/packages/`` by
default) so the robot can be loaded via a local path later.

Unlike the session cache used by ``Robot.load("arsenal:...")``, installed
packages survive process restarts.
"""

from __future__ import annotations

from pathlib import Path

from bulletlab.arsenal.downloader import download_package
from bulletlab.arsenal.exceptions import ArsenalError
from bulletlab.arsenal.paths import DEFAULT_PACKAGES_DIR
from bulletlab.arsenal.resolver import parse_source, resolve_model, resolve_package


def install(
    source: str,
    path: str | Path | None = None,
) -> Path:
    """Install an Arsenal robot package to a permanent local directory.

    Downloads only the URDF and mesh files required by the requested model,
    not the entire package.

    Args:
        source: One of:

            * ``"package_name"`` — installs the package's default model.
            * ``"package_name/model_id"`` — installs a specific model.
            * ``"https://..."`` — reserved for future URL support (not yet
              implemented; raises :class:`~bulletlab.arsenal.exceptions.ArsenalError`).

        path: Optional destination directory.  When omitted, the package is
            installed to ``~/.bulletlab/packages/<package_name>/``.

    Returns:
        :class:`pathlib.Path` to the installed URDF file.

    Raises:
        ArsenalError: On any resolution, network, or download failure.

    Example::

        # Install the default model of reference_bot
        Robot.install("reference_bot")

        # Install a specific model to a project-local directory
        Robot.install("reference_bot/BLem1", path="robots/")
    """
    if source.startswith("http://") or source.startswith("https://"):
        raise ArsenalError(
            "Direct URL installation is not yet supported. "
            "Please use 'package_name' or 'package_name/model_id'."
        )

    package_name, model_id = parse_source(source)

    # Resolve against the live registry
    resolve_package(package_name)   # validates the package exists
    model = resolve_model(package_name, model_id)
    entrypoint: str = model["entrypoint"]

    # Determine install directory
    if path is None:
        dest_dir = DEFAULT_PACKAGES_DIR / package_name
    else:
        dest_dir = Path(path) / package_name

    dest_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"[BulletLab Arsenal] Installing {package_name!r} "
        f"(model: {model.get('display_name', model_id or 'default')}) "
        f"→ {dest_dir}"
    )

    urdf_path = download_package(package_name, entrypoint, dest_dir)

    print(f"[BulletLab Arsenal] Installed: {urdf_path}")
    return urdf_path
