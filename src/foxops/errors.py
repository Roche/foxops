class FoxopsError(Exception):
    """Base class for all foxops errors."""


class IncarnationNotFoundError(FoxopsError):
    """Exception raised when an Incarnation cannot be found in the inventory"""

    def __init__(self, incarnation_id: int):
        super().__init__(f"Incarnation with id '{incarnation_id}' not found.")


class IncarnationRepositoryNotFound(FoxopsError):
    """Exception raised when the remote Incarnation repository cannot be found"""

    def __init__(self, incarnation_repository: str):
        self.incarnation_repository = incarnation_repository
        super().__init__(
            f"Incarnation repository '{incarnation_repository}' not found."
        )


class IncarnationAlreadyExistsError(FoxopsError):
    """Exception raised when an Incarnation already exists in the inventory"""

    def __init__(self, incarnation_repository: str, target_directory: str):
        super().__init__(
            f"Incarnation at '{incarnation_repository}' and target directory '{target_directory}' already exists."
        )


class RetryableError(FoxopsError):
    """Exception raised when an error occurs for which a retry usually helps."""


class ReconciliationError(FoxopsError):
    """Exception raised when an error occurs during reconciliation."""
