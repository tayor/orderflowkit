"""Async stream protocol."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol


class BaseAsyncStream(Protocol):
    """Protocol for async normalized event streams."""

    def __aiter__(self) -> AsyncIterator[dict[str, object]]:
        """Return an async iterator of normalized events."""
