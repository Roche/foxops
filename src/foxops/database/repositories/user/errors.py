from typing import Optional

from foxops.errors import FoxopsError


class UserNotFoundError(FoxopsError):
    def __init__(self, id: Optional[int] = None, username: Optional[str] = None):
        if id is None and username is None:
            raise ValueError("id or username must be provided")
        if id is not None and username is not None:
            raise ValueError("id and username cannot both be provided")
        if id is not None:
            super().__init__(f"User with id '{id}' not found.")
        else:
            super().__init__(f"User with username '{username}' not found.")


class UserAlreadyExistsError(Exception):
    def __init__(self, username: str):
        super().__init__(f"User with username '{username}' already exists.")


class UserOwnerOfResourcesError(FoxopsError):
    def __init__(self, id: int):
        super().__init__(
            f"User with id '{id}' is the owner of resources and cannot be deleted. Delete the resources first."
        )
