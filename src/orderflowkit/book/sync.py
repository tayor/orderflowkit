"""Sequence synchronization helpers."""

from __future__ import annotations


def has_sequence_gap(
    last_update_id: int | None, first_update_id: int | None, update_id: int | None
) -> bool:
    """Return true when an incoming update does not connect to the current sequence."""

    if last_update_id is None or update_id is None:
        return False
    expected = last_update_id + 1
    if first_update_id is not None:
        return first_update_id > expected
    return update_id > expected
