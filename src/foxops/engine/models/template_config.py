"""
Pydantic Models (TemplateConfig) that can be used for reading the `fengine.yaml` file in a Template root directory.
"""

import abc
import re
from pathlib import Path
from typing import Annotated, Any, Literal, Self, Type, Union

from pydantic import (
    AfterValidator,
    BaseModel,
    Field,
    ValidationError,
    create_model,
    model_validator,
)
from ruamel.yaml import YAML


class BaseVariableDefinition(BaseModel, abc.ABC):
    description: str
    default: Any | None = None

    def is_required(self) -> bool:
        return self.default is None

    @abc.abstractmethod
    def value_model(self) -> Any:
        """
        Returns the object that can be used in a pydantic model field definition for representing the data
        of this variable.
        """

        ...


class StringVariableDefinition(BaseVariableDefinition):
    type: Literal["str", "string"] = "string"
    default: str | None = None

    def value_model(self) -> Any:
        return str


class IntegerVariableDefinition(BaseVariableDefinition):
    type: Literal["int", "integer"] = "integer"
    default: int | None = None

    def value_model(self) -> Any:
        return int


class BooleanVariableDefinition(BaseVariableDefinition):
    type: Literal["boolean"] = "boolean"
    default: bool | None = None

    def value_model(self) -> Any:
        return bool


class BaseListVariableDefinition(BaseVariableDefinition):
    type: Literal["list"] = "list"


class StringListVariableDefinition(BaseListVariableDefinition):
    element_type: Literal["string"] = "string"

    default: list[str] | None = None

    def value_model(self) -> Any:
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

    default: dict[str, Any] | None = None

    def value_model(self) -> Type[BaseModel]:
        fields: dict[str, Any] = {
            name: (child.value_model(), ... if child.default is None else child.default)
            for name, child in self.children.items()
        }
        return create_model("ObjectVariable", **fields)

    @model_validator(mode="after")
    def validate_default(self) -> Self:
        if self.default is not None:
            try:
                self.value_model().model_validate(self.default)
            except ValidationError as e:
                raise ValueError(f"default value does not match the specified children schema ({e.errors()})") from e

        return self


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
            name: (var.value_model(), ... if var.default is None else var.default)
            for name, var in self.variables.items()
        }
        return create_model("TemplateDataModel", **fields)

    def save(self, target: Path) -> None:
        yaml = YAML(typ="safe")
        yaml.default_flow_style = False

        with target.open("w") as f:
            yaml.dump(self.model_dump(), f)
