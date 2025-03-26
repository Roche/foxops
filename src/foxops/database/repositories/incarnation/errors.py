class IncarnationNotFoundError(Exception):
    def __init__(self, id: int):
        self.id = id
        super().__init__(f"Incarnation with id '{id}' not found.")


class IncarnationAlreadyExistsError(Exception):
    pass
