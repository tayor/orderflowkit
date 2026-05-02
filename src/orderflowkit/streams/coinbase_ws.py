"""Coinbase public L2 stream placeholder."""

from __future__ import annotations

from collections.abc import AsyncIterator

from orderflowkit.utils.exceptions import OptionalDependencyError


class CoinbaseLevel2Stream:
    """Coinbase level2 adapter reserved for the multi-exchange release."""

    def __init__(self, symbol: str, *, depth: int = 100) -> None:
        self.symbol = symbol
        self.depth = depth

    async def events(self) -> AsyncIterator[dict[str, object]]:
        """Raise a clear message for the not-yet-implemented adapter."""

        raise OptionalDependencyError(
            "CoinbaseLevel2Stream is planned but not implemented in 0.1.0"
        )
        yield {}

    def __aiter__(self) -> AsyncIterator[dict[str, object]]:
        return self.events()
