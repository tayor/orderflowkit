"""Order-book validation helpers."""

from __future__ import annotations

from orderflowkit.book.local_book import LocalBook


def is_crossed(book: LocalBook) -> bool:
    """Return whether a local book is crossed."""

    return book.is_crossed()


def has_both_sides(book: LocalBook) -> bool:
    """Return whether both bid and ask sides contain at least one level."""

    return bool(book.bids and book.asks)
