import copy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Annotated, Mapping

from pydantic import BaseModel, ConfigDict, Field
from ruamel.yaml import YAML

from foxops.logger import get_logger

#: Holds the module logger
logger = get_logger(__name__)

yaml = YAML(typ="safe")
yaml.default_flow_style = False


#: Holds the type for all `template_data` dictionary values
TemplateDataValue = str | int | float
#: Holds the type for all `template_data` dictionaries
TemplateData = Mapping[str, TemplateDataValue]


@dataclass(frozen=True)
class IncarnationState:
    """Represents an Incarnation State record.

    The incarnation state is recorded for every incarnation in `.fengine.yaml`
    relative to the incarnation target directory.

    Use the `load_incarnation_state` and `save_incarnation_state` below to
    load and save the incarnation from and to the file system.
    """

    #: Holds a reference to the template repository.
    #: This may be a local path or a Git URL.
    template_repository: str
    #: Holds a version of the template repository
    template_repository_version: str
    #: Holds a git sha of the template repository the `template_repository_version` points to
    template_repository_version_hash: str
    #: Holds a dict of string key value pairs which have been used to
    #: as template render data.
    template_data: TemplateData


def save_incarnation_state(incarnation_state_path: Path, incarnation_state: IncarnationState) -> None:
    with incarnation_state_path.open("w") as f:
        f.write("# This file is auto-generated and owned by foxops.\n")
        f.write("# DO NOT EDIT MANUALLY.\n")
        yaml.dump(asdict(incarnation_state), f)


def load_incarnation_state(incarnation_state_path: Path) -> IncarnationState:
    with incarnation_state_path.open("r") as f:
        raw_state = yaml.load(f)
    return IncarnationState(**raw_state)


def load_incarnation_state_from_string(incarnation_state: str) -> IncarnationState:
    raw_state = yaml.load(incarnation_state)
    return IncarnationState(**raw_state)


class VariableDefinition(BaseModel):
    type: str = Field(..., description="The type of the variable")
    description: str = Field(..., help="The description for this variable")
    default: Annotated[
        TemplateDataValue | None,
        Field(help="The default value for this variable (setting this makes the variable optional)"),
    ] = None

    model_config = ConfigDict(frozen=True)

    def is_required(self) -> bool:
        return self.default is None


class TemplateRenderingConfig(BaseModel):
    excluded_files: list[str] = Field(
        default_factory=list,
        description="List of filenames (relative to template/ directory) of which the content should not be rendered using Jinja. "
        "Glob patterns are supported, but must match the individual files. Use '**/*' to match everything recursively.",
    )

    model_config = ConfigDict(frozen=True)


class TemplateConfig(BaseModel):
    """Represents the configuration of a template.

    Example:

    ```yaml
    required_foxops_version: v1.0.0

    variables:
        name:
            description: the name of the project
            type: str

        number:
            description: same number
            type: int
    ```
    """

    required_foxops_version: str = "v0.0.0"
    rendering: TemplateRenderingConfig = Field(default_factory=TemplateRenderingConfig)

    variables: dict[str, VariableDefinition] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)

    @property
    def required_variables(self) -> dict[str, VariableDefinition]:
        return {k: v for k, v in self.variables.items() if v.is_required()}

    @property
    def optional_variables_defaults(self) -> TemplateData:
        return {k: v.default for k, v in self.variables.items() if v.default is not None}

    def to_yaml(self, target: Path) -> None:
        with target.open("w") as f:
            yaml.dump(self.model_dump(), f)


def load_template_config(template_config_path: Path) -> TemplateConfig:
    try:
        with template_config_path.open("r") as f:
            raw_state = yaml.load(f)
        return TemplateConfig(**raw_state)
    except FileNotFoundError:
        return TemplateConfig()


def fill_missing_optionals_with_defaults(
    provided_template_data: TemplateData,
    template_config: TemplateConfig,
) -> TemplateData:
    provided_variable_names = set(provided_template_data.keys())
    config_variable_names = set(template_config.variables.keys())
    template_data_with_defaults = dict(copy.deepcopy(provided_template_data))
    optional_vars = template_config.optional_variables_defaults
    if need_default := config_variable_names.difference(provided_variable_names):
        logger.debug(
            f"Given template data is missing the values for the optional variables {need_default}, using defaults for those"
        )
        for key in (k for k in need_default if k in optional_vars):
            template_data_with_defaults[key] = optional_vars[key]

    return template_data_with_defaults
