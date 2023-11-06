from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel
from ruamel.yaml import YAML

from foxops.logger import get_logger

#: Holds the module logger
logger = get_logger(__name__)


TemplateData = dict[str, Any]


class IncarnationState(BaseModel):
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

    # Holds the template data that was provided by the user as input
    template_data: TemplateData
    # Holds all template data that was used when rendering the templates. This includes the user provided data,
    # as well as other values added through variable defaults or fengine itself.
    template_data_full: TemplateData

    @classmethod
    def from_file(cls, path: Path) -> Self:
        return cls.from_string(path.read_text())

    @classmethod
    def from_string(cls, content: str) -> Self:
        obj = YAML(typ="safe").load(content)

        # support reading legacy incarnation state files (<= foxops v2.2)
        if "template_data_full" not in obj:
            obj["template_data_full"] = obj["template_data"]

        return cls.model_validate(obj)

    def save(self, path: Path) -> None:
        yaml = YAML(typ="safe")
        yaml.default_flow_style = False

        logger.debug(f"save incarnation state to {path} after template initialization")
        with path.open("w") as f:
            f.write("# This file is auto-generated and owned by foxops.\n")
            f.write("# DO NOT EDIT MANUALLY.\n")
            yaml.dump(self.model_dump(), f)
