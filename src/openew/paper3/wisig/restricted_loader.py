"""Restricted reader for the official WiSig compact pickle container.

Pickle is not intrinsically safe.  This module permits only the small set of
NumPy reconstruction globals needed by array-only compact WiSig objects and
rejects persistent IDs, extension hooks, and every other global.
"""

from __future__ import annotations

import io
import pickle
from pathlib import Path
from typing import Any, BinaryIO

import numpy as np


class RestrictedPickleError(pickle.UnpicklingError):
    """Raised when a serialized object requests a non-allowlisted operation."""


_ALLOWED_GLOBALS: dict[tuple[str, str], object] = {
    ("numpy", "dtype"): np.dtype,
    ("numpy", "ndarray"): np.ndarray,
    ("numpy.core.multiarray", "_reconstruct"): np.core.multiarray._reconstruct,
    ("numpy._core.multiarray", "_reconstruct"): np.core.multiarray._reconstruct,
    ("numpy.core.multiarray", "scalar"): np.core.multiarray.scalar,
    ("numpy._core.multiarray", "scalar"): np.core.multiarray.scalar,
}


class RestrictedUnpickler(pickle.Unpickler):
    """Fail-closed unpickler for primitive containers and NumPy arrays."""

    def find_class(self, module: str, name: str) -> object:
        key = (module, name)
        try:
            return _ALLOWED_GLOBALS[key]
        except KeyError as exc:
            raise RestrictedPickleError(
                f"forbidden pickle global: {module}.{name}"
            ) from exc

    def persistent_load(self, pid: object) -> object:
        raise RestrictedPickleError(f"persistent pickle IDs are forbidden: {pid!r}")


def _validate_tree(value: object, *, max_depth: int = 12, _depth: int = 0) -> None:
    """Validate the reconstructed tree without invoking user-defined hooks."""

    if _depth > max_depth:
        raise RestrictedPickleError("serialized object exceeds maximum nesting depth")
    if value is None or isinstance(value, (str, bytes, bool, int, float, complex)):
        return
    if isinstance(value, np.generic):
        return
    if isinstance(value, np.ndarray):
        if value.dtype.hasobject:
            raise RestrictedPickleError("object-dtype NumPy arrays are forbidden")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_tree(key, max_depth=max_depth, _depth=_depth + 1)
            _validate_tree(item, max_depth=max_depth, _depth=_depth + 1)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _validate_tree(item, max_depth=max_depth, _depth=_depth + 1)
        return
    raise RestrictedPickleError(f"forbidden reconstructed type: {type(value)!r}")


def restricted_load(file_or_path: str | Path | BinaryIO) -> Any:
    """Load a compact dataset using the restricted NumPy allowlist.

    The official compact container is a single pickle object, so deserialization
    is necessarily whole-object.  Downstream conversion is shard-bounded.
    """

    close = False
    if isinstance(file_or_path, (str, Path)):
        stream: BinaryIO = Path(file_or_path).open("rb")
        close = True
    elif isinstance(file_or_path, io.BufferedIOBase) or hasattr(file_or_path, "read"):
        stream = file_or_path  # type: ignore[assignment]
    else:
        raise TypeError("file_or_path must be a path or binary file object")
    try:
        value = RestrictedUnpickler(stream).load()
        trailing = stream.read(1)
        if trailing:
            raise RestrictedPickleError("trailing bytes follow the serialized object")
        _validate_tree(value)
        return value
    except RestrictedPickleError:
        raise
    except (pickle.UnpicklingError, EOFError, AttributeError, ValueError) as exc:
        raise RestrictedPickleError(f"invalid restricted pickle: {exc}") from exc
    finally:
        if close:
            stream.close()
