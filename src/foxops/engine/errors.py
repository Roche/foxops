from pydantic import ValidationError

from foxops.errors import FoxopsUserError


class ProvidedTemplateDataInvalidError(FoxopsUserError):
    def get_readable_error_messages(self) -> list[str]:
        if not isinstance(self.__cause__, ValidationError):
            raise RuntimeError(
                "exception was not chained. Must be raised (raise ... from ...) " "with a ValidationError as cause"
            )

        validation_error = self.__cause__

        error_messages: list[str] = []
        for e in validation_error.errors():
            match e:
                case {"type": "missing"}:
                    location = ".".join(map(lambda x: str(x), e["loc"]))
                    error_messages.append(f"'{location}' - no value was provided for this required template variable")
                case _:
                    error_messages.append(str(e))

        return error_messages
