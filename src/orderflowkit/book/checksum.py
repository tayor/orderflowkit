"""Checksum helpers for venues that publish book checksums."""

from __future__ import annotations

import zlib
from collections.abc import Iterable


def crc32_checksum(parts: Iterable[str]) -> int:
    """Compute an unsigned CRC32 checksum from ordered string parts."""

    payload = ":".join(parts).encode("utf-8")
    return zlib.crc32(payload) & 0xFFFFFFFF
