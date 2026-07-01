"""
Exceptions raised by the BulletLab Arsenal integration.

All Arsenal-specific errors inherit from ``ArsenalError`` so callers can
catch the full family with a single ``except ArsenalError``.
"""

from __future__ import annotations


class ArsenalError(Exception):
    """Base class for all BulletLab Arsenal errors."""


class PackageNotFoundError(ArsenalError):
    """Raised when a requested Arsenal package does not exist in the registry.

    Example::

        raise PackageNotFoundError("unitree_g1")
    """


class ModelNotFoundError(ArsenalError):
    """Raised when a requested model ID does not exist inside a package.

    Example::

        raise ModelNotFoundError("g1_29dof", package="unitree_g1")
    """


class NetworkError(ArsenalError):
    """Raised when a network request to the Arsenal repository fails.

    Wraps the underlying ``urllib`` or OS-level error for inspection.
    """


class ManifestError(ArsenalError):
    """Raised when the Arsenal manifest or package metadata is missing,
    malformed, or incompatible with the current Arsenal schema version.
    """


class CorruptedPackageError(ArsenalError):
    """Raised when a downloaded file is missing, empty, or otherwise
    does not match the expected structure of an Arsenal package.
    """
