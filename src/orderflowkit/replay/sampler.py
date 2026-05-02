"""Replay sampling helpers."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import islice
from typing import TypeVar

T = TypeVar("T")


def take_every(values: Iterable[T], step: int) -> list[T]:
    """Return every Nth item from an iterable."""

    return list(islice(values, 0, None, step))
