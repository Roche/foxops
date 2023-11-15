"""
Pydantic Models (TemplateConfig) that can be used for reading the `fengine.yaml` file in a Template root directory.
"""

import abc
import re
from io import StringIO
from pathlib import Path
from typing import Annotated, Any, Literal, Self, Type, Union

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    Field,
    ValidationError,
    create_model,
)
from ruamel.yaml import YAML


class BaseVariableDefinition(BaseModel, abc.ABC):
    description: str

    @abc.abstractmethod
    def pydantic_field_default(self) -> Any:
        """
        Returns the default value that can be used in a pydantic model field definition for this variable.
        """

        ...

    @abc.abstractmethod
    def pydantic_field_model(self) -> Any:
        """
        Returns the object that can be used in a pydantic model field definition for representing the data
        of this variable.
        """

        ...


class BaseFlatVariableDefinition(BaseVariableDefinition):
    default: Any | None = None

    def pydantic_field_default(self) -> Any:
        return self.default if self.default is not None else ...


def convert_to_string(v: Any) -> str:
    if isinstance(v, (int, float, bool)):
        return str(v)
    return v


class StringVariableDefinition(BaseFlatVariableDefinition):
    type: Literal["str", "string"] = "string"
    default: str | None = None

    def pydantic_field_model(self) -> Any:
        return Annotated[str, BeforeValidator(convert_to_string)]


class IntegerVariableDefinition(BaseFlatVariableDefinition):
    type: Literal["int", "integer"] = "integer"
    default: int | None = None

    def pydantic_field_model(self) -> Any:
        return int


class BooleanVariableDefinition(BaseFlatVariableDefinition):
    type: Literal["bool", "boolean"] = "boolean"
    default: bool | None = None

    def pydantic_field_model(self) -> Any:
        return bool


class BaseListVariableDefinition(BaseFlatVariableDefinition):
    type: Literal["list"] = "list"


class StringListVariableDefinition(BaseListVariableDefinition):
    element_type: Literal["string"] = "string"

    default: list[str] | None = None

    def pydantic_field_model(self) -> Any:
        return list[str]


VariableDefinition = Annotated[
    Union[
        StringVariableDefinition,
        IntegerVariableDefinition,
        BooleanVariableDefinition,
        StringListVariableDefinition,
        "ObjectVariableDefinition",
    ],
    Field(..., discriminator="type"),
]


def valid_variable_names(v: dict[str, Any]) -> dict[str, Any]:
    variable_name_pattern = re.compile(r"[a-zA-Z][a-zA-Z0-9_]*")
    for variable_name in v.keys():
        if not variable_name_pattern.fullmatch(variable_name):
            raise ValueError(
                f"variable name '{variable_name}' contains characters that are not allowed "
                f"(only letters, digits and underscores are valid)"
            )

    return v


VariableDefinitions = Annotated[dict[str, VariableDefinition], AfterValidator(valid_variable_names)]


class ObjectVariableDefinition(BaseVariableDefinition):
    type: Literal["object"] = "object"
    children: VariableDefinitions

    def pydantic_field_default(self) -> Any:
        try:
            return self.pydantic_field_model()()
        except ValidationError:
            return ...

    def pydantic_field_model(self) -> Type[BaseModel]:
        fields: dict[str, Any] = {
            name: (child.pydantic_field_model(), child.pydantic_field_default())
            for name, child in self.children.items()
        }
        return create_model("ObjectVariable", **fields)


class TemplateRenderingConfig(BaseModel):
    excluded_files: list[str] = Field(
        default_factory=list,
        description="List of filenames (relative to template/ directory) of which the content should not be rendered using Jinja. "
        "Glob patterns are supported, but must match the individual files. Use '**/*' to match everything recursively.",
    )


class TemplateConfig(BaseModel):
    rendering: TemplateRenderingConfig = Field(default_factory=TemplateRenderingConfig)

    variables: VariableDefinitions = Field(default_factory=dict)

    @classmethod
    def from_path(cls, path: Path) -> Self:
        if path.is_file():
            yaml = YAML(typ="safe")
            obj = yaml.load(path.read_text())

            return cls(**obj)

        return cls()

    def data_model(self) -> Type[BaseModel]:
        """
        Returns a pydantic model that can be used to validate template data that is provided for rendering
        this template.
        """

        fields: dict[str, Any] = {
            name: (var.pydantic_field_model(), var.pydantic_field_default()) for name, var in self.variables.items()
        }
        return create_model("TemplateDataModel", **fields)

    def save(self, target: Path) -> None:
        target.write_text(self.yaml())

    def yaml(self) -> str:
        yaml = YAML(typ="safe")
        yaml.default_flow_style = False

        s = StringIO()
        yaml.dump(self.model_dump(), s)

        return s.getvalue()
