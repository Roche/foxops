from foxops.errors import FoxopsError


class ChangeConflictError(FoxopsError):
    def __init__(self, incarnation_id: int, revision: int) -> None:
        super().__init__(f"Change with revision {revision} already exists for incarnation {incarnation_id}")


class ChangeNotFoundError(FoxopsError):
    def __init__(self, id_: int) -> None:
        super().__init__(f"Change with id {id_} not found")


class ChangeCommitAlreadyPushedError(FoxopsError):
    def __init__(self, id_: int) -> None:
        super().__init__(
            f"The commit for change with id {id_} was already pushed. Then the commit sha cannot be changed."
        )


class IncarnationHasNoChangesError(FoxopsError):
    def __init__(self, incarnation_id: int) -> None:
        super().__init__(f"Incarnation with id {incarnation_id} has no changes")
