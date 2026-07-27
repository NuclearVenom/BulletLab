"""
Package and model resolution for BulletLab Arsenal.

Fetches the robot manifest from the Arsenal registry and translates a
user-supplied ``"package_name"`` or ``"package_name/model_id"`` string into
a concrete model entry with a known ``entrypoint`` URDF path.

The manifest is fetched once per Python session and cached in-memory so
that multiple ``Robot.load("arsenal:...")`` calls do not hammer the network.
"""

from __future__ import annotations

from bulletlab.arsenal.client import fetch_json
from bulletlab.arsenal.exceptions import (
    ManifestError,
    ModelNotFoundError,
    PackageNotFoundError,
)
from bulletlab.arsenal.paths import (
    ARSENAL_PACKAGE_METADATA_URL,
    ARSENAL_ROBOTS_MANIFEST_URL,
)

# ---------------------------------------------------------------------------
# In-memory manifest cache (cleared when the process exits)
# ---------------------------------------------------------------------------

_manifest_cache: dict | None = None
_metadata_cache: dict[str, dict] = {}


def _get_manifest() -> dict:
    """Return the Arsenal robot manifest, fetching it if necessary.

    Returns:
        Parsed manifest ``dict`` with a ``"packages"`` list.

    Raises:
        ManifestError: If the manifest cannot be fetched or parsed.
    """
    global _manifest_cache
    if _manifest_cache is None:
        try:
            import time
            # Append timestamp to bypass GitHub's 5-minute raw content cache
            url = f"{ARSENAL_ROBOTS_MANIFEST_URL}?t={int(time.time())}"
            _manifest_cache = fetch_json(url)
        except Exception as exc:
            raise ManifestError(
                f"Could not fetch the Arsenal robot manifest: {exc}\n"
                f"URL: {ARSENAL_ROBOTS_MANIFEST_URL}"
            ) from exc
    return _manifest_cache


def _get_package_metadata(package_name: str) -> dict:
    """Return the ``metadata.json`` for *package_name*, fetching if necessary.

    Args:
        package_name: Exact package directory name (e.g. ``"reference_bot"``).

    Returns:
        Parsed metadata ``dict``.

    Raises:
        ManifestError: If the metadata cannot be fetched or parsed.
    """
    if package_name not in _metadata_cache:
        url = ARSENAL_PACKAGE_METADATA_URL.format(package_name=package_name)
        try:
            _metadata_cache[package_name] = fetch_json(url)
        except Exception as exc:
            raise ManifestError(
                f"Could not fetch metadata for package {package_name!r}: {exc}\n"
                f"URL: {url}"
            ) from exc
    return _metadata_cache[package_name]


# ---------------------------------------------------------------------------
# Public resolution API
# ---------------------------------------------------------------------------


def parse_source(source: str) -> tuple[str, str | None]:
    """Parse a user-supplied Arsenal source string.

    Accepted formats:
    * ``"package_name"``               → ``("package_name", None)``
    * ``"package_name/model_id"``      → ``("package_name", "model_id")``

    Args:
        source: The raw source string **without** the ``"arsenal:"`` prefix.

    Returns:
        A ``(package_name, model_id_or_none)`` tuple.
    """
    source = source.strip()
    
    try:
        manifest = _get_manifest()
        packages = manifest.get("packages", [])
        pkg_names = [p.get("package_name") for p in packages if p.get("package_name")]
        
        # Sort by length descending to match the longest package path first
        # This handles nested package names like "unitree/g1_description" correctly
        for pkg_name in sorted(pkg_names, key=len, reverse=True):
            if source == pkg_name:
                return pkg_name, None
            if source.startswith(pkg_name + "/"):
                model_id = source[len(pkg_name) + 1:]
                return pkg_name, model_id
    except Exception:
        pass  # Fallback to naive parsing if manifest cannot be loaded
        
    # Fallback logic for flat structures or offline errors
    parts = source.split("/", 1)
    pkg = parts[0].strip()
    model = parts[1].strip() if len(parts) > 1 else None
    return pkg, model


def resolve_package(package_name: str) -> dict:
    """Look up *package_name* in the Arsenal manifest.

    Args:
        package_name: The package directory name (e.g. ``"reference_bot"``).

    Returns:
        The package entry ``dict`` from the manifest ``"packages"`` list.

    Raises:
        PackageNotFoundError: If no package with that name exists.
        ManifestError: If the manifest is unavailable or malformed.

    Example::

        pkg = resolve_package("reference_bot")
        print(pkg["display_name"])   # "BLem1"
    """
    manifest = _get_manifest()
    packages: list[dict] = manifest.get("packages", [])
    for entry in packages:
        if entry.get("package_name") == package_name:
            return entry
    available = [e.get("package_name", "?") for e in packages]
    raise PackageNotFoundError(
        f"Arsenal package {package_name!r} not found in the registry.\n"
        f"Available packages: {available}"
    )


def resolve_model(package_name: str, model_id: str | None) -> dict:
    """Resolve a model entry from a package's ``metadata.json``.

    When *model_id* is ``None``, the package's default model is returned
    (the entry with ``"default": true``, or the first model if none is
    explicitly marked as default).

    Args:
        package_name: The package directory name.
        model_id: Requested model ``id``, or ``None`` for the default.

    Returns:
        The model entry ``dict`` containing at least ``"id"`` and
        ``"entrypoint"``.

    Raises:
        ModelNotFoundError: If the requested model ID does not exist.
        ManifestError: If the package metadata cannot be fetched.

    Example::

        model = resolve_model("reference_bot", None)
        print(model["entrypoint"])   # "urdf/BLem1.urdf"
    """
    metadata = _get_package_metadata(package_name)
    models: list[dict] = metadata.get("models", [])

    if not models:
        raise ManifestError(
            f"Package {package_name!r} has no models listed in metadata.json."
        )

    if model_id is None:
        # Return the default model
        for m in models:
            if m.get("default", False):
                return m
        return models[0]  # fall back to first

    # Exact match on id or display_name (case-insensitive)
    model_id_lower = model_id.lower()
    for m in models:
        if (
            m.get("id", "").lower() == model_id_lower
            or m.get("display_name", "").lower() == model_id_lower
        ):
            return m

    available = [m.get("id", "?") for m in models]
    raise ModelNotFoundError(
        f"Model {model_id!r} not found in Arsenal package {package_name!r}.\n"
        f"Available models: {available}"
    )
