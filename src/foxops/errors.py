from typing import Optional


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


class ForbiddenError(FoxopsError):
    pass


class ResourceForbiddenError(ForbiddenError):
    """Exception raised when a user is not allowed to access a certain resource"""

    def __init__(self, message: Optional[str] = None):
        message = message or "You are not allowed to perfom the action on this resource"
        super().__init__(message)


class GeneralForbiddenError(ForbiddenError):
    """Exception raised when a user is not allowed to perform a certain action"""

    def __init__(self, message: str):
        super().__init__(message)
