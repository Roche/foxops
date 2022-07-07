class FoxopsError(Exception):
    """Base Exception for all Foxops specific errors."""


class RetryableError(FoxopsError):
    """Exception raised when an error occurs for which a retry usually helps."""
