"""Compatibility shims for third-party libraries.

The AoE2ScenarioParser byte serializer calls ``int.to_bytes`` on every integer
field it writes. Our map layers are numpy-backed, so some field values arrive
as numpy integer scalars (``np.int64``, ``np.int32``, ``np.uint8``, ...), which
do **not** implement ``to_bytes`` and are not ``int`` subclasses. This causes
``AttributeError: 'numpy.int64' object has no attribute 'to_bytes'`` when
saving a scenario.

Rather than coerce every field at every call site (fragile — new fields keep
appearing), we patch the parser's ``int_to_bytes`` helper once, at import time,
to coerce its input to a native Python ``int`` first. The patch is idempotent
and a no-op for values that are already plain ints.
"""

from __future__ import annotations

import numpy as np

# Guard so repeated imports (e.g. in tests) don't re-patch.
_applied = False


def _coerce_int(value: object) -> int:
    """Return ``value`` as a native Python int.

    Handles numpy integer scalars, plain ints, and int-likes. Floats are
    truncated (the parser only ever passes integer-typed fields here).
    """
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, int):
        return value
    # Last resort: anything with an __int__ (e.g. bool, other numeric types).
    return int(value)


def apply_numpy_compat() -> None:
    """Patch AoE2ScenarioParser's byte serializer to be numpy-safe.

    Idempotent: safe to call multiple times.
    """
    global _applied
    if _applied:
        return

    try:
        from AoE2ScenarioParser.helper import bytes_conversions
    except ImportError:  # pragma: no cover - parser is a hard dependency
        return

    original = bytes_conversions.int_to_bytes

    def int_to_bytes(
        integer: int, length: int, endian: str = "little", signed: bool = True
    ) -> bytes:
        return original(_coerce_int(integer), length, endian=endian, signed=signed)

    bytes_conversions.int_to_bytes = int_to_bytes
    _applied = True


apply_numpy_compat()
