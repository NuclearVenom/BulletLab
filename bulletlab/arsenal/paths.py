"""
Platform-independent path constants and URL roots for BulletLab Arsenal.

All URLs and local directory defaults are defined here so that changing the
repository location or the local install prefix requires editing a single file.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Remote — GitHub raw content
# ---------------------------------------------------------------------------

#: GitHub organisation / repository hosting the Arsenal package registry.
ARSENAL_GITHUB_REPO: str = "NuclearVenom/bulletlab-arsenal"

#: Base URL for raw file access in the Arsenal repository (default branch).
ARSENAL_BASE_URL: str = (
    f"https://raw.githubusercontent.com/{ARSENAL_GITHUB_REPO}/main"
)

#: URL of the category-level robot manifest (lists all robot packages).
ARSENAL_ROBOTS_MANIFEST_URL: str = f"{ARSENAL_BASE_URL}/robots/manifest.json"

#: URL template for a package's metadata.json.
#: Call ``.format(package_name=...)`` to resolve.
ARSENAL_PACKAGE_METADATA_URL: str = (
    f"{ARSENAL_BASE_URL}/robots/{{package_name}}/metadata.json"
)

#: URL template for a file inside a package.
#: Call ``.format(package_name=..., rel_path=...)`` to resolve.
ARSENAL_PACKAGE_FILE_URL: str = (
    f"{ARSENAL_BASE_URL}/robots/{{package_name}}/{{rel_path}}"
)

# ---------------------------------------------------------------------------
# Local — install destination
# ---------------------------------------------------------------------------

#: Default permanent install directory.
#: Resolves to ``~/.bulletlab/packages/`` on all platforms.
DEFAULT_PACKAGES_DIR: Path = Path.home() / ".bulletlab" / "packages"
