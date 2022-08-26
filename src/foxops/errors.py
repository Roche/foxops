class FoxopsError(Exception):
    """Base class for all foxops errors."""


class FoxopsUserError(FoxopsError):
    """Base class for all foxops errors that are caused by user input."""


class RetryableError(FoxopsError):
    """Exception raised when an error occurs for which a retry usually helps."""


class ReconciliationError(FoxopsError):
    """Exception raised when an error occurs during reconciliation."""


class ReconciliationUserError(ReconciliationError, FoxopsUserError):
    """Exception raised when a user error occurs during reconciliation."""


class IncarnationNotFoundError(FoxopsError):
    """Exception raised when an Incarnation cannot be found in the inventory"""

    def __init__(self, incarnation_id: int):
        super().__init__(f"Incarnation with id '{incarnation_id}' not found.")


class IncarnationRepositoryNotFound(FoxopsError):
    """Exception raised when the remote Incarnation repository cannot be found"""

    def __init__(self, incarnation_repository: str):
        self.incarnation_repository = incarnation_repository
        super().__init__(f"Incarnation repository '{incarnation_repository}' not found.")


class IncarnationAlreadyInitializedError(ReconciliationUserError):
    """Exception raised when an Incarnation already exists in the inventory"""

    def __init__(
        self,
        incarnation_repository: str,
        target_directory: str,
        commit_sha: str,
        has_mismatch: bool,
    ):
        self.commit_sha = commit_sha
        self.has_mismatch = has_mismatch
        super().__init__(
            f"Incarnation at '{incarnation_repository}' and target directory '{target_directory}' already initialized."
        )
