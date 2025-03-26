from typing import Optional

from foxops.errors import FoxopsError


class GroupNotFoundError(FoxopsError):
    def __init__(self, system_name: Optional[str] = None, id: Optional[int] = None):
        if system_name is None and id is None:
            raise ValueError("system_name or id must be provided")
        if system_name is not None and id is not None:
            raise ValueError("system_name and id cannot both be provided")
        if system_name is not None:
            self.system_name = system_name
            super().__init__(f"Group with system name '{system_name}' not found.")
        else:
            self.id = id
            super().__init__(f"Group with id '{id}' not found.")


class GroupAlreadyExistsError(FoxopsError):
    def __init__(self, system_name: str):
        self.system_name = system_name
        super().__init__(f"Group with System name ${system_name} already exists")
