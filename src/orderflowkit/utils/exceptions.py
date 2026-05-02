"""Package-specific exceptions."""


class OrderFlowKitError(Exception):
    """Base exception for all OrderFlowKit errors."""


class DataValidationError(OrderFlowKitError):
    """Raised when input market data is missing required fields or contains invalid values."""


class OptionalDependencyError(OrderFlowKitError):
    """Raised when an optional dependency is needed for the requested operation."""


class BookSequenceError(OrderFlowKitError):
    """Raised when an order-book sequence gap is detected in strict mode."""
