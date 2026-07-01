"""
HTTP client for BulletLab Arsenal.

Provides thin wrappers around ``urllib`` that raise descriptive
:class:`~bulletlab.arsenal.exceptions.NetworkError` exceptions instead of
raw ``urllib`` errors.

Only the standard library is used — no ``requests`` dependency required.
"""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from bulletlab.arsenal.exceptions import NetworkError

# Default timeout for all Arsenal HTTP requests (seconds).
_TIMEOUT: int = 30


def fetch_bytes(url: str) -> bytes:
    """Download the raw bytes at *url*.

    Args:
        url: The full URL to fetch.

    Returns:
        Raw response body as :class:`bytes`.

    Raises:
        NetworkError: On any HTTP or connection error.

    Example::

        data = fetch_bytes("https://raw.githubusercontent.com/.../BLem1.urdf")
    """
    try:
        with urlopen(url, timeout=_TIMEOUT) as resp:
            return resp.read()
    except HTTPError as exc:
        raise NetworkError(
            f"HTTP {exc.code} while fetching {url!r}: {exc.reason}"
        ) from exc
    except URLError as exc:
        raise NetworkError(
            f"Network error while fetching {url!r}: {exc.reason}"
        ) from exc
    except Exception as exc:
        raise NetworkError(
            f"Unexpected error while fetching {url!r}: {exc}"
        ) from exc


def fetch_json(url: str) -> dict:
    """Download and parse a JSON document at *url*.

    Args:
        url: The full URL to a JSON resource.

    Returns:
        Parsed JSON as a :class:`dict`.

    Raises:
        NetworkError: On any HTTP, connection, or JSON parse error.

    Example::

        manifest = fetch_json(
            "https://raw.githubusercontent.com/.../robots/manifest.json"
        )
    """
    raw = fetch_bytes(url)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise NetworkError(
            f"Failed to parse JSON from {url!r}: {exc}"
        ) from exc
